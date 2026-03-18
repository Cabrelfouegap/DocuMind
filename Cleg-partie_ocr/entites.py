# entites.py
"""
entites.py
Extraction des entités nommées (NER) via spaCy + regex pour données admin françaises
Detecte : noms, dates, montants, SIRET/SIREN, numéros de TVA, adresses
"""

import re
import spacy

# Modèle spaCy français (moyen = bon équilibre taille/précision)

_nlp = None


def get_nlp():
    """
    Charge le modèle spaCy une seule fois
    """
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("fr_core_news_md")
        except OSError:
            
            # Fallback sur le petit modèle si le moyen n'est pas installé

            print("[NER] Modèle 'fr_core_news_md' absent → essai avec fr_core_news_sm")
            _nlp = spacy.load("fr_core_news_sm")
    return _nlp


# Regex pour les champs admin typiques des documents français

PATTERNS_REGEX = {
    "siret": r"\b\d{14}\b",
    "siren": r"\b\d{9}\b",
    "tva_intra": r"\bFR\s*\d{2}\s*\d{9}\b",
    "montant": r"\b\d[\d\s]*[,.]\d{2}\s*(?:€|EUR|euros?)",
    "date": r"\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b",
    "email": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "tel": r"\b(?:\+33|0)\s*[1-9](?:[\s\-\.]?\d{2}){4}\b",
    "iban": r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}\b",
    "bic": r"\b[A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b",
}


def _dedoublonner(valeurs: list) -> list:
    """
    Supprime les doublons en conservant l'ordre d'apparition
    """
    resultat = []
    deja_vus = set()

    for valeur in valeurs:
        valeur = valeur.strip()
        if valeur and valeur not in deja_vus:
            resultat.append(valeur)
            deja_vus.add(valeur)

    return resultat


def _premier_ou_vide(valeurs: list) -> str:
    """
    Retourne la première valeur trouvée ou une chaîne vide
    """
    return valeurs[0] if valeurs else ""


def _normaliser_iban(valeur: str) -> str:
    """
    Supprime les espaces d'un IBAN
    """
    return re.sub(r"\s+", "", valeur).upper().strip()


def _normaliser_montant(valeur: str) -> str:
    """
    Nettoie légèrement un montant pour homogénéiser la sortie
    """
    return valeur.replace("EUR", "€").replace("euros", "€").strip()


def extraire_regex(texte: str) -> dict:
    """
    Extraction par regex des champs admin (SIRET, TVA, montants, dates, etc.)
    Retourne un dict {type: [liste_valeurs]}
    """
    extraits = {}

    for nom, pattern in PATTERNS_REGEX.items():
        trouvailles = re.findall(pattern, texte, re.IGNORECASE)

        if nom == "iban":
            trouvailles = [_normaliser_iban(v) for v in trouvailles]
        else:
            trouvailles = [v.strip() for v in trouvailles]

        trouvailles = _dedoublonner(trouvailles)

        if trouvailles:
            extraits[nom] = trouvailles

    return extraits


def extraire_ner_spacy(texte: str) -> dict:
    """
    Extraction via NER spaCy : personnes, organisations, lieux
    Retourne un dict {type_entite: [liste_valeurs]}
    """
    nlp = get_nlp()

    # spaCy a une limite de taille — on coupe si trop long

    texte_tronque = texte[:100000] if len(texte) > 100000 else texte
    doc = nlp(texte_tronque)

    entites = {}

    # PER=personne, ORG=organisation, LOC=lieu, MISC=divers

    for ent in doc.ents:
        cat = ent.label_
        if cat not in entites:
            entites[cat] = []
        valeur = ent.text.strip()
        if valeur not in entites[cat]:
            entites[cat].append(valeur)

    return entites


def classer_doc(texte: str) -> str:
    """
    Classifie le type de document selon les mots-clés présents
    Retourne : "quote" | "invoice" | "urssaf" | "kbis" | "rib" | "unknown"
    """
    texte_min = texte.lower()

    if "relevé d'identité bancaire" in texte_min or "releve d'identite bancaire" in texte_min:
        return "rib"
    if "iban" in texte_min and "bic" in texte_min:
        return "rib"

    if "kbis" in texte_min or "extrait kbis" in texte_min or "registre du commerce" in texte_min:
        return "kbis"

    if "urssaf" in texte_min or "attestation de vigilance" in texte_min:
        return "urssaf"

    if "devis" in texte_min:
        return "quote"

    if "facture" in texte_min:
        return "invoice"

    return "unknown"


def _chercher_premiere_occurrence(pattern: str, texte: str, flags=0) -> str:
    """
    Retourne la première sous-chaîne correspondant au pattern ou une chaîne vide
    """
    match = re.search(pattern, texte, flags)
    if match:
        if match.lastindex:
            return match.group(1).strip()
        return match.group(0).strip()
    return ""


def _extraire_nom_societe(entites_regex: dict, entites_ner: dict, texte: str) -> str:
    """
    Détermine un nom de société plausible
    Priorité : ORG spaCy puis quelques formulations fréquentes
    """
    orgs = entites_ner.get("ORG", [])
    if orgs:
        return orgs[0]

    patterns = [
        r"(?:société|societe|entreprise|raison sociale)\s*[:\-]\s*([^\n]+)",
        r"(?:émise par|emise par|fournisseur|prestataire)\s*[:\-]?\s*([^\n]+)",
        r"^([A-Z][A-Z0-9&\-\.\s]{2,})$",
    ]

    for pattern in patterns:
        valeur = _chercher_premiere_occurrence(pattern, texte, flags=re.IGNORECASE | re.MULTILINE)
        if valeur:
            return valeur

    return ""


def _extraire_bank_name(entites_ner: dict, texte: str) -> str:
    """
    Extrait un nom de banque
    """
    orgs = entites_ner.get("ORG", [])
    for org in orgs:
        if any(mot in org.lower() for mot in ["banque", "bank", "credit", "caisse", "société générale", "societe generale", "bnp", "lcl"]):
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


def _extraire_numero(patterns: list, texte: str) -> str:
    """
    Extrait un numéro via une liste de patterns ordonnés
    """
    for pattern in patterns:
        valeur = _chercher_premiere_occurrence(pattern, texte, flags=re.IGNORECASE)
        if valeur:
            return valeur
    return ""


def _extraire_dates(entites_regex: dict) -> list:
    """
    Retourne la liste des dates détectées
    """
    return entites_regex.get("date", [])


def _extraire_montants(entites_regex: dict) -> list:
    """
    Retourne la liste des montants détectés
    """
    return [_normaliser_montant(v) for v in entites_regex.get("montant", [])]


def _extraire_taux_tva(texte: str) -> str:
    """
    Extrait le taux de TVA
    """
    patterns = [
        r"(?:tva|taux de tva)\s*[:\-]?\s*(\d{1,2}(?:[.,]\d{1,2})?\s*%)",
    ]

    for pattern in patterns:
        valeur = _chercher_premiere_occurrence(pattern, texte, flags=re.IGNORECASE)
        if valeur:
            return valeur.replace(" ", "")

    return ""


def _extraire_description_produit(texte: str) -> str:
    """
    Tente d'extraire une description de produit ou prestation
    """
    patterns = [
        r"(?:objet|description|désignation|designation|prestation|produit)\s*[:\-]\s*([^\n]+)",
    ]

    for pattern in patterns:
        valeur = _chercher_premiere_occurrence(pattern, texte, flags=re.IGNORECASE)
        if valeur:
            return valeur

    return ""


def _extraire_adresse(texte: str) -> str:
    """
    Extrait une adresse simple sur une ligne
    """
    patterns = [
        r"(?:adresse|siege social|siège social)\s*[:\-]\s*([^\n]+)",
    ]

    for pattern in patterns:
        valeur = _chercher_premiere_occurrence(pattern, texte, flags=re.IGNORECASE)
        if valeur:
            return valeur

    return ""


def _extraire_forme_juridique(texte: str) -> str:
    """
    Extrait une forme juridique si elle apparaît
    """
    patterns = [
        r"\b(SASU|SAS|SARL|EURL|SCI|SA|SNC|EI|EIRL|micro-entreprise|auto-entrepreneur)\b"
    ]

    for pattern in patterns:
        valeur = _chercher_premiere_occurrence(pattern, texte, flags=re.IGNORECASE)
        if valeur:
            return valeur.upper()

    return ""


def _extraire_titulaires(entites_ner: dict, texte: str) -> str:
    """
    Extrait le titulaire / détenteur du compte pour un RIB
    """
    patterns = [
        r"(?:titulaire|account holder|bénéficiaire|beneficiaire)\s*[:\-]\s*([^\n]+)",
    ]

    for pattern in patterns:
        valeur = _chercher_premiere_occurrence(pattern, texte, flags=re.IGNORECASE)
        if valeur:
            return valeur

    pers = entites_ner.get("PER", [])
    if pers:
        return pers[0]

    orgs = entites_ner.get("ORG", [])
    if orgs:
        return orgs[0]

    return ""


def extraire_champs_metier(texte: str, type_document: str, entites_regex: dict, entites_ner: dict) -> dict:
    """
    Extrait les champs métier normalisés attendus par la suite du pipeline
    """
    company_name = _extraire_nom_societe(entites_regex, entites_ner, texte)
    siret = _premier_ou_vide(entites_regex.get("siret", []))
    dates = _extraire_dates(entites_regex)
    montants = _extraire_montants(entites_regex)
    tva_rate = _extraire_taux_tva(texte)

    champs = {}

    if type_document == "quote":
        champs = {
            "company_name": company_name,
            "siret": siret,
            "quote_number": _extraire_numero(
                [
                    r"(?:devis|quote)\s*(?:n[°o]?\s*)?[:\-]?\s*([A-Z0-9\-_\/]+)",
                ],
                texte
            ),
            "product_description": _extraire_description_produit(texte),
            "amount_ht": montants[0] if len(montants) > 0 else "",
            "vat_rate": tva_rate,
            "total_ttc": montants[-1] if montants else "",
            "quote_issue_date": dates[0] if len(dates) > 0 else "",
            "quote_validity_date": _extraire_numero(
                [
                    r"(?:valable jusqu[’']au|date de validité|date de validite|validité jusqu[’']au)\s*[:\-]?\s*(\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4})",
                ],
                texte
            ) or (dates[1] if len(dates) > 1 else ""),
        }

    elif type_document == "invoice":
        champs = {
            "company_name": company_name,
            "siret": siret,
            "invoice_number": _extraire_numero(
                [
                    r"(?:facture|invoice)\s*(?:n[°o]?\s*)?[:\-]?\s*([A-Z0-9\-_\/]+)",
                ],
                texte
            ),
            "product_description": _extraire_description_produit(texte),
            "amount_ht": montants[0] if len(montants) > 0 else "",
            "vat_rate": tva_rate,
            "total_ttc": montants[-1] if montants else "",
            "invoice_issue_date": dates[0] if dates else "",
        }

    elif type_document == "urssaf":
        champs = {
            "company_name": company_name,
            "siret": siret,
            "certificate_number": _extraire_numero(
                [
                    r"(?:attestation|certificat|numéro d[’']attestation|numero d[’']attestation|n[°o]\s*d[’']attestation)\s*[:\-]?\s*([A-Z0-9\-_\/]+)",
                ],
                texte
            ),
            "issue_date": dates[0] if len(dates) > 0 else "",
            "expiration_date": _extraire_numero(
                [
                    r"(?:valable jusqu[’']au|date d[’']expiration|expiration)\s*[:\-]?\s*(\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4})",
                ],
                texte
            ) or (dates[1] if len(dates) > 1 else ""),
        }

    elif type_document == "kbis":
        champs = {
            "company_name": company_name,
            "siret": siret,
            "legal_form": _extraire_forme_juridique(texte),
            "creation_date": _extraire_numero(
                [
                    r"(?:date de création|date de creation|immatriculée le|immatriculee le|créée le|cree le)\s*[:\-]?\s*(\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4})",
                ],
                texte
            ) or (dates[0] if dates else ""),
            "address": _extraire_adresse(texte),
        }

    elif type_document == "rib":
        champs = {
            "bank_name": _extraire_bank_name(entites_ner, texte),
            "iban": _premier_ou_vide(entites_regex.get("iban", [])),
            "bic": _premier_ou_vide(entites_regex.get("bic", [])),
            "account_holder": _extraire_titulaires(entites_ner, texte),
        }

    return champs


def extraire_entites(texte: str) -> dict:
    """
    Combine NER spaCy + regex pour extraire toutes les entités utiles
    Retourne un dict complet avec toutes les entités trouvées
    """
    entites_regex = extraire_regex(texte)
    entites_nlp = extraire_ner_spacy(texte)
    type_doc = classer_doc(texte)
    champs_metier = extraire_champs_metier(
        texte=texte,
        type_document=type_doc,
        entites_regex=entites_regex,
        entites_ner=entites_nlp
    )

    return {
        "type_document": type_doc,
        "entites_regex": entites_regex,
        "entites_ner": entites_nlp,
        "champs_metier": champs_metier,
    }