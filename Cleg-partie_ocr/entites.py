# entites.py
"""
Extraction des entités nommées (NER) + regex + champs métier
"""

import re
import spacy
from datetime import datetime 

_nlp = None


def get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("fr_core_news_md")
        except OSError:
            print("[NER] Modèle 'fr_core_news_md' absent → fallback fr_core_news_sm")
            _nlp = spacy.load("fr_core_news_sm")
    return _nlp


PATTERNS_REGEX = {
    "siret": r"\b(?:\d[\s ]*){14}\b",
    "siren": r"\b(?:\d[\s ]*){9}\b",
    "tva_intra": r"\bFR\s*\d{2}\s*\d{9}\b",
    "montant": r"\b\d[\d\s.,]*\d\s*(?:€|EUR|euros?)",
    "date": r"\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b|\b\d{4}[\/\-\. ]\d{1,2}[\/\-\. ]\d{1,2}\b",
    "email": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "tel": r"\b(?:\+33|0)\s*[1-9](?:[\s\-\.]?\d{2}){4}\b",
    "iban": r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}\b",
    "bic": r"\b[A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b",
}


def _dedoublonner(valeurs: list) -> list:
    resultat = []
    deja_vus = set()
    for valeur in valeurs:
        valeur = valeur.strip()
        if valeur and valeur not in deja_vus:
            resultat.append(valeur)
            deja_vus.add(valeur)
    return resultat


def _premier_ou_vide(valeurs: list) -> str:
    return valeurs[0] if valeurs else ""


def _normaliser_iban(valeur: str) -> str:
    return re.sub(r"\s+", "", valeur).upper().strip()


def _normaliser_montant(valeur: str) -> str:
    valeur = valeur.replace("EUR", "€").replace("euros", "€").strip()
    valeur = re.sub(r"\s+", " ", valeur)
    return valeur


def _valider_luhn(nombre: str) -> bool:
    if not nombre or not nombre.isdigit():
        return False

    total = 0
    chiffres = nombre[::-1]

    for i, c in enumerate(chiffres):
        n = int(c)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n

    return total % 10 == 0


def _normaliser_siret(valeur: str) -> str:
    if not valeur:
        return ""
    chiffres = re.sub(r"\D", "", valeur)
    if len(chiffres) == 14 and _valider_luhn(chiffres):
        return chiffres
    return ""


def _normaliser_date_si_valide(valeur: str) -> str:
    """
    Garde la valeur seulement si elle correspond à une vraie date.
    Accepte les séparateurs / - . et espace.
    Sinon renvoie une chaîne vide.
    """
    if not valeur:
        return ""

    valeur = valeur.strip()
    valeur = re.sub(r"\s+", " ", valeur)

    # Uniformise les séparateurs pour tester proprement
    normalisee = re.sub(r"[.\- ]", "/", valeur)

    formats = [
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%d/%m/%y",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(normalisee, fmt)
            # On renvoie au format ISO propre
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return ""


def extraire_regex(texte: str) -> dict:
    extraits = {}

    for nom, pattern in PATTERNS_REGEX.items():
        trouvailles = re.findall(pattern, texte, re.IGNORECASE)

        if nom == "iban":
            trouvailles = [_normaliser_iban(v) for v in trouvailles]
        elif nom == "siret":
            trouvailles = [_normaliser_siret(v) for v in trouvailles]
            trouvailles = [v for v in trouvailles if v]
        elif nom == "siren":
            trouvailles = [re.sub(r"\D", "", v).strip() for v in trouvailles]
            trouvailles = [v for v in trouvailles if len(v) == 9]
        elif nom == "montant":
            trouvailles = [_normaliser_montant(v) for v in trouvailles]
        else:
            trouvailles = [v.strip() for v in trouvailles]

        trouvailles = _dedoublonner(trouvailles)

        if trouvailles:
            extraits[nom] = trouvailles

    return extraits


def extraire_ner_spacy(texte: str) -> dict:
    nlp = get_nlp()
    texte_tronque = texte[:100000] if len(texte) > 100000 else texte
    doc = nlp(texte_tronque)

    entites = {}
    for ent in doc.ents:
        cat = ent.label_
        if cat not in entites:
            entites[cat] = []
        valeur = ent.text.strip()
        if valeur not in entites[cat]:
            entites[cat].append(valeur)

    return entites


def classer_doc(texte: str) -> str:
    texte_min = texte.lower()

    if (
        "relevé d'identité bancaire" in texte_min
        or "releve d'identite bancaire" in texte_min
        or "\nrib" in texte_min
        or ("iban" in texte_min and "bic" in texte_min)
        or ("bank" in texte_min and "account holder" in texte_min)
    ):
        return "rib"

    if (
        "kbis" in texte_min
        or "kbis extract" in texte_min
        or "legal form" in texte_min
        or "extrait kbis" in texte_min
    ):
        return "kbis"

    if (
        "urssaf" in texte_min
        or "attestation de vigilance" in texte_min
        or "urssaf certificate" in texte_min
        or ("certificate number" in texte_min and "expiration date" in texte_min)
    ):
        return "urssaf"

    if "devis" in texte_min or "quote" in texte_min or "quote number" in texte_min:
        return "quote"

    if "facture" in texte_min or "invoice" in texte_min or "invoice number" in texte_min:
        return "invoice"

    return "unknown"


def _nettoyer_valeur_extraite(valeur: str) -> str:
    if not valeur:
        return ""

    valeur = valeur.strip()
    valeur = re.sub(r"\s+", " ", valeur)

    faux_positifs = {"value", "field", "label", "info", "data"}
    if valeur.lower() in faux_positifs:
        return ""

    return valeur


def _extraire_valeur_apres_label(texte: str, labels: list[str]) -> str:
    if not texte or not labels:
        return ""

    for label in labels:
        pattern = rf"(?:^|\n)\s*{re.escape(label)}\s*[:\-]?\s*(.+?)(?=\n|$)"
        match = re.search(pattern, texte, flags=re.IGNORECASE)
        if match:
            valeur = _nettoyer_valeur_extraite(match.group(1))
            if valeur and valeur.lower() != label.lower():
                return valeur

    return ""


def _chercher_premiere_occurrence(pattern: str, texte: str, flags=0) -> str:
    match = re.search(pattern, texte, flags)
    if match:
        if match.lastindex:
            return match.group(1).strip()
        return match.group(0).strip()
    return ""


def _ressemble_a_date(valeur: str) -> bool:
    if not valeur:
        return False

    valeur = valeur.strip().lower()
    valeur = re.sub(r"\s+", " ", valeur)

    if valeur in {"date", "invoice date", "quote date"}:
        return True

    patterns = [
        r"date\s*[:\-]?\s*\d{4}[\/\-. ]\d{1,2}[\/\-. ]\d{1,2}",
        r"date\s*[:\-]?\s*\d{1,2}[\/\-. ]\d{1,2}[\/\-. ]\d{2,4}",
        r"\d{4}[\/\-. ]\d{1,2}[\/\-. ]\d{1,2}",
        r"\d{1,2}[\/\-. ]\d{1,2}[\/\-. ]\d{2,4}",
    ]
    return any(re.fullmatch(p, valeur) for p in patterns)


def _extraire_nom_societe(entites_ner: dict, texte: str) -> str:
    valeur = _extraire_valeur_apres_label(
        texte,
        ["Company", "Société", "Societe", "Raison sociale"]
    )
    if valeur:
        return valeur

    orgs = entites_ner.get("ORG", []) if entites_ner else []
    if orgs:
        return orgs[0]

    patterns = [
        r"(?:société|societe|entreprise|raison sociale)\s*[:\-]\s*([^\n]+)",
        r"(?:émise par|emise par|fournisseur|prestataire)\s*[:\-]?\s*([^\n]+)",
    ]
    for pattern in patterns:
        valeur = _chercher_premiere_occurrence(pattern, texte, flags=re.IGNORECASE)
        if valeur:
            return valeur

    return ""


def _extraire_bank_name(entites_ner: dict, texte: str) -> str:
    valeur = _extraire_valeur_apres_label(texte, ["Bank", "Banque"])
    if valeur:
        return valeur

    orgs = entites_ner.get("ORG", []) if entites_ner else []
    for org in orgs:
        if any(mot in org.lower() for mot in ["banque", "bank", "credit", "postal", "bnp", "caisse", "lcl"]):
            return org

    patterns = [
        r"(?:banque|bank)\s*[:\-]\s*([^\n]+)",
        r"^(?:banque|bank)\s+([^\n]+)$",
    ]
    for pattern in patterns:
        valeur = _chercher_premiere_occurrence(pattern, texte, flags=re.IGNORECASE | re.MULTILINE)
        if valeur:
            return valeur

    return ""


def _extraire_dates(entites_regex: dict) -> list:
    return entites_regex.get("date", [])


def _extraire_montants(entites_regex: dict) -> list:
    return [_normaliser_montant(v) for v in entites_regex.get("montant", [])]


def _extraire_taux_tva(texte: str) -> str:
    patterns = [
        r"(?:tva|vat|taux de tva)\s*[:\-]?\s*(\d{1,2}(?:[.,]\d{1,2})?\s*%)",
    ]
    for pattern in patterns:
        valeur = _chercher_premiere_occurrence(pattern, texte, flags=re.IGNORECASE)
        if valeur:
            return valeur.replace(" ", "")
    return ""


def _extraire_description_produit(texte: str) -> str:
    valeur = _extraire_valeur_apres_label(
        texte,
        ["Product", "Description", "Produit", "Prestation", "Désignation", "Designation"]
    )
    if valeur:
        return valeur

    patterns = [
        r"(?:objet|description|désignation|designation|prestation|produit)\s*[:\-]\s*([^\n]+)",
    ]
    for pattern in patterns:
        valeur = _chercher_premiere_occurrence(pattern, texte, flags=re.IGNORECASE)
        if valeur:
            return valeur
    return ""


def _extraire_adresse(texte: str) -> str:
    valeur = _extraire_valeur_apres_label(
        texte,
        ["Address", "Adresse", "Siege social", "Siège social"]
    )
    if valeur:
        return valeur

    patterns = [
        r"(?:adresse|siege social|siège social)\s*[:\-]\s*([^\n]+)",
    ]
    for pattern in patterns:
        valeur = _chercher_premiere_occurrence(pattern, texte, flags=re.IGNORECASE)
        if valeur:
            return valeur
    return ""


def _extraire_forme_juridique(texte: str) -> str:
    valeur = _extraire_valeur_apres_label(
        texte,
        ["Legal Form", "Forme juridique"]
    )
    if valeur:
        return valeur.upper()

    patterns = [r"\b(SASU|SAS|SARL|EURL|SCI|SA|SNC|EI|EIRL|micro-entreprise|auto-entrepreneur)\b"]
    for pattern in patterns:
        valeur = _chercher_premiere_occurrence(pattern, texte, flags=re.IGNORECASE)
        if valeur:
            return valeur.upper()
    return ""


def _extraire_titulaires(entites_ner: dict, texte: str) -> str:
    valeur = _extraire_valeur_apres_label(
        texte,
        ["Account Holder", "Titulaire", "Bénéficiaire", "Beneficiaire"]
    )
    if valeur:
        return valeur

    patterns = [
        r"(?:titulaire|account holder|bénéficiaire|beneficiaire)\s*[:\-]\s*([^\n]+)",
    ]
    for pattern in patterns:
        valeur = _chercher_premiere_occurrence(pattern, texte, flags=re.IGNORECASE)
        if valeur:
            return valeur

    pers = entites_ner.get("PER", []) if entites_ner else []
    if pers:
        return pers[0]

    orgs = entites_ner.get("ORG", []) if entites_ner else []
    if orgs:
        return orgs[0]

    return ""


def _extraire_numero(patterns: list[str], texte: str) -> str:
    for pattern in patterns:
        valeur = _chercher_premiere_occurrence(pattern, texte, flags=re.IGNORECASE)
        if valeur:
            return valeur
    return ""


def extraire_champs_metier(texte: str, type_document: str, entites_regex: dict, entites_ner: dict) -> dict:
    siret_label = _extraire_valeur_apres_label(texte, ["SIRET", "Siret"])
    siret_regex = _premier_ou_vide(entites_regex.get("siret", []))
    siret = _normaliser_siret(siret_label or siret_regex)

    company_name = _extraire_nom_societe(entites_ner, texte)
    dates = _extraire_dates(entites_regex)
    montants = _extraire_montants(entites_regex)
    tva_rate = _extraire_taux_tva(texte)

    champs = {}

    if type_document == "quote":
        quote_number = _extraire_valeur_apres_label(texte, ["Quote Number"]) or _extraire_numero(
            [
                r"(?:quote number|numéro de devis|numero de devis)\s*[:\-]?\s*([A-Z0-9\-_\/]+)",
                r"(?:devis n[°o]?|quote n[°o]?)\s*[:\-]?\s*([A-Z0-9\-_\/]+)",
            ],
            texte
        )
        if _ressemble_a_date(quote_number):
            quote_number = ""

        champs = {
            "company_name": company_name,
            "siret": siret,
            "quote_number": quote_number,
            "product_description": _extraire_description_produit(texte),
            "amount_ht": _extraire_valeur_apres_label(texte, ["Amount HT", "Montant HT"]) or (montants[0] if len(montants) > 0 else ""),
            "vat_rate": _extraire_valeur_apres_label(texte, ["VAT", "TVA"]) or tva_rate,
            "total_ttc": _extraire_valeur_apres_label(texte, ["Total TTC"]) or (montants[-1] if montants else ""),
            "quote_issue_date": _normaliser_date_si_valide(
                _extraire_valeur_apres_label(texte, ["Quote Date", "Date devis", "Date"]) or (dates[0] if len(dates) > 0 else "")
            ),
            "quote_validity_date": _normaliser_date_si_valide(
                _extraire_valeur_apres_label(texte, ["Validity Date", "Date de validité", "Valable jusqu'au"]) or (dates[1] if len(dates) > 1 else "")
            ),
        }

    elif type_document == "invoice":
        invoice_number = _extraire_valeur_apres_label(texte, ["Invoice Number"]) or _extraire_numero(
            [
                r"(?:invoice number|numéro de facture|numero de facture)\s*[:\-]?\s*([A-Z0-9\-_\/]+)",
                r"(?:facture n[°o]?|invoice n[°o]?)\s*[:\-]?\s*([A-Z0-9\-_\/]+)",
            ],
            texte
        )
        if _ressemble_a_date(invoice_number):
            invoice_number = ""

        champs = {
            "company_name": company_name,
            "siret": siret,
            "invoice_number": invoice_number,
            "product_description": _extraire_description_produit(texte),
            "amount_ht": _extraire_valeur_apres_label(texte, ["Amount HT", "Montant HT"]) or (montants[0] if len(montants) > 0 else ""),
            "vat_rate": _extraire_valeur_apres_label(texte, ["VAT", "TVA"]) or tva_rate,
            "total_ttc": _extraire_valeur_apres_label(texte, ["Total TTC"]) or (montants[-1] if montants else ""),
            "invoice_issue_date": _normaliser_date_si_valide(
                _extraire_valeur_apres_label(texte, ["Date", "Invoice Date"]) or (dates[0] if dates else "")
            ),
        }

    elif type_document == "urssaf":
        champs = {
            "company_name": company_name,
            "siret": siret,
            "certificate_number": _extraire_valeur_apres_label(texte, ["Certificate Number", "Numéro d'attestation"]) or _extraire_numero(
                [r"(?:attestation|certificat|numéro d[’']attestation|numero d[’']attestation|n[°o]\s*d[’']attestation)\s*[:\-]?\s*([A-Z0-9\-_\/]+)"],
                texte
            ),
            "issue_date": _normaliser_date_si_valide(
                _extraire_valeur_apres_label(texte, ["Issue Date", "Date d'émission"]) or (dates[0] if len(dates) > 0 else "")
            ),
            "expiration_date": _normaliser_date_si_valide(
                _extraire_valeur_apres_label(texte, ["Expiration Date", "Date d'expiration"]) or (dates[1] if len(dates) > 1 else "")
            ),
        }

    elif type_document == "kbis":
        champs = {
            "company_name": company_name,
            "siret": siret,
            "legal_form": _extraire_forme_juridique(texte),
            "creation_date": _normaliser_date_si_valide(
                _extraire_valeur_apres_label(texte, ["Creation Date", "Date de création"]) or (dates[0] if dates else "")
            ),
            "address": _extraire_adresse(texte),
        }

    elif type_document == "rib":
        titulaire = _extraire_titulaires(entites_ner, texte)
        champs = {
            "company_name": company_name or titulaire,
            "siret": siret,
            "bank_name": _extraire_bank_name(entites_ner, texte),
            "iban": _extraire_valeur_apres_label(texte, ["IBAN"]) or _premier_ou_vide(entites_regex.get("iban", [])),
            "bic": _extraire_valeur_apres_label(texte, ["BIC"]) or _premier_ou_vide(entites_regex.get("bic", [])),
            "account_holder": titulaire,
        }

    return champs


def extraire_entites(texte: str) -> dict:
    entites_regex = extraire_regex(texte)
    entites_nlp = extraire_ner_spacy(texte)
    type_doc = classer_doc(texte)
    champs_metier = extraire_champs_metier(
        texte=texte,
        type_document=type_doc,
        entites_regex=entites_regex,
        entites_ner=entites_nlp,
    )

    return {
        "type_document": type_doc,
        "entites_regex": entites_regex,
        "entites_ner": entites_nlp,
        "champs_metier": champs_metier,
    }