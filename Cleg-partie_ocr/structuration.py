# structuration.py
"""
Construction du JSON final standardisé
"""

import os
import hashlib
from datetime import datetime


def calc_hash(chemin_fichier: str) -> str:
    hasher = hashlib.md5()
    with open(chemin_fichier, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def _base_champs_par_type(type_document: str) -> dict:
    mapping = {
        "quote": {
            "company_name": "",
            "siret": "",
            "quote_number": "",
            "product_description": "",
            "amount_ht": "",
            "vat_rate": "",
            "total_ttc": "",
            "quote_issue_date": "",
            "quote_validity_date": "",
        },
        "invoice": {
            "company_name": "",
            "siret": "",
            "invoice_number": "",
            "product_description": "",
            "amount_ht": "",
            "vat_rate": "",
            "total_ttc": "",
            "invoice_issue_date": "",
        },
        "urssaf": {
            "company_name": "",
            "siret": "",
            "certificate_number": "",
            "issue_date": "",
            "expiration_date": "",
        },
        "kbis": {
            "company_name": "",
            "siret": "",
            "legal_form": "",
            "creation_date": "",
            "address": "",
        },
        "rib": {
            "company_name": "",
            "siret": "",
            "bank_name": "",
            "iban": "",
            "bic": "",
            "account_holder": "",
        },
    }
    return mapping.get(type_document, {})


def _extraire_confiance_ocr(taux_erreur: dict | None = None):
    if not taux_erreur:
        return ""

    if "confiance_estimee_pct" in taux_erreur:
        return taux_erreur["confiance_estimee_pct"]

    if "cer_pct" in taux_erreur:
        return round(max(0.0, 100.0 - float(taux_erreur["cer_pct"])), 2)

    return ""


def _normaliser_score_confiance(ocr_confidence):
    if ocr_confidence in ("", None):
        return 0.0

    try:
        score = float(ocr_confidence)
    except (TypeError, ValueError):
        return 0.0

    if 0 <= score <= 1:
        return round(score, 4)

    if 0 <= score <= 100:
        return round(score / 100, 4)

    return 0.0


def _ajuster_confiance_selon_champs(document_json: dict, score_base: float) -> float:
    champs_critiques = {
        "invoice": [
            "company_name", "siret", "invoice_number",
            "amount_ht", "vat_rate", "total_ttc", "invoice_issue_date"
        ],
        "quote": [
            "company_name", "siret", "quote_number",
            "amount_ht", "vat_rate", "total_ttc",
            "quote_issue_date", "quote_validity_date"
        ],
        "urssaf": [
            "company_name", "siret", "certificate_number",
            "issue_date", "expiration_date"
        ],
        "kbis": [
            "company_name", "siret", "legal_form",
            "creation_date", "address"
        ],
        "rib": [
            "bank_name", "iban", "bic", "account_holder"
        ],
    }

    type_document = document_json.get("document_type", "unknown")
    champs = champs_critiques.get(type_document, [])

    if not champs:
        return round(max(0.0, min(1.0, score_base - 0.5)), 4)

    nb_manquants = sum(1 for champ in champs if not document_json.get(champ, ""))
    ratio_manquants = nb_manquants / len(champs)
    score_final = score_base - (ratio_manquants * 0.85)

    if type_document == "unknown":
        score_final -= 0.2

    if type_document in {"invoice", "quote", "kbis", "urssaf"} and not document_json.get("siret", ""):
        score_final -= 0.1

    if type_document == "invoice" and not document_json.get("invoice_number", ""):
        score_final -= 0.05

    if type_document == "quote" and not document_json.get("quote_number", ""):
        score_final -= 0.05

    return round(max(0.0, min(1.0, score_final)), 4)


def construire_json(
    chemin_fichier: str,
    texte_brut: str,
    texte_propre: str,
    entites: dict,
    taux_erreur: dict | None = None,
) -> dict:
    nom_fichier = os.path.basename(chemin_fichier)
    ext = nom_fichier.lower().split(".")[-1]
    hash_md5 = calc_hash(chemin_fichier)
    type_document = entites.get("type_document", "unknown")

    regex_data = entites.get("entites_regex", {})
    ner_data = entites.get("entites_ner", {})
    champs_metier = entites.get("champs_metier", {})

    resultat = {
        "document_id": hash_md5,
        # vendor_id sera recalculé plus bas à partir du SIRET / nom si possible
        "vendor_id": "",
        "file_name": nom_fichier,
        "document_type": type_document,
        "ocr_confidence": _extraire_confiance_ocr(taux_erreur),
    }

    base_champs = _base_champs_par_type(type_document)
    base_champs.update(champs_metier)
    resultat.update(base_champs)

    resultat["meta"] = {
        "nom_fichier": nom_fichier,
        "extension": ext,
        "hash_md5": hash_md5,
        "date_traitement": datetime.now().isoformat(),
        "type_document": type_document,
    }

    resultat["texte_brut"] = texte_brut
    resultat["texte_propre"] = texte_propre

    resultat["champs_admin"] = {
        "siret": regex_data.get("siret", []),
        "siren": regex_data.get("siren", []),
        "tva_intra": regex_data.get("tva_intra", []),
        "montants": regex_data.get("montant", []),
        "dates": regex_data.get("date", []),
        "emails": regex_data.get("email", []),
        "telephones": regex_data.get("tel", []),
        "iban": regex_data.get("iban", []),
        "bic": regex_data.get("bic", []),
    }

    resultat["entites_ner"] = {
        "personnes": ner_data.get("PER", []),
        "organisations": ner_data.get("ORG", []),
        "lieux": ner_data.get("LOC", []),
        "divers": ner_data.get("MISC", []),
    }

    resultat["qualite_ocr"] = taux_erreur if taux_erreur else {}

    resultat["validation"] = {
        "statut": "en_attente",
        "anomalies": [],
    }

    return resultat


def construire_payload_vendor(document_json: dict, vendor_id: str = "") -> dict:
    type_document = document_json.get("document_type", "unknown")
    score_base = _normaliser_score_confiance(document_json.get("ocr_confidence", ""))
    score_final = _ajuster_confiance_selon_champs(document_json, score_base)

    document_sortie = {
        "document_type": type_document,
        "ocr_confidence": score_final,
    }

    if type_document == "quote":
        document_sortie.update({
            "company_name": document_json.get("company_name", ""),
            "siret": document_json.get("siret", ""),
            "quote_number": document_json.get("quote_number", ""),
            "product_description": document_json.get("product_description", ""),
            "amount_ht": document_json.get("amount_ht", ""),
            "vat_rate": document_json.get("vat_rate", ""),
            "total_ttc": document_json.get("total_ttc", ""),
            "quote_issue_date": document_json.get("quote_issue_date", ""),
            "quote_validity_date": document_json.get("quote_validity_date", ""),
        })

    elif type_document == "invoice":
        document_sortie.update({
            "company_name": document_json.get("company_name", ""),
            "siret": document_json.get("siret", ""),
            "invoice_number": document_json.get("invoice_number", ""),
            "product_description": document_json.get("product_description", ""),
            "amount_ht": document_json.get("amount_ht", ""),
            "vat_rate": document_json.get("vat_rate", ""),
            "total_ttc": document_json.get("total_ttc", ""),
            "invoice_issue_date": document_json.get("invoice_issue_date", ""),
        })

    elif type_document == "urssaf":
        document_sortie.update({
            "company_name": document_json.get("company_name", ""),
            "siret": document_json.get("siret", ""),
            "certificate_number": document_json.get("certificate_number", ""),
            "issue_date": document_json.get("issue_date", ""),
            "expiration_date": document_json.get("expiration_date", ""),
        })

    elif type_document == "kbis":
        document_sortie.update({
            "company_name": document_json.get("company_name", ""),
            "siret": document_json.get("siret", ""),
            "legal_form": document_json.get("legal_form", ""),
            "creation_date": document_json.get("creation_date", ""),
            "address": document_json.get("address", ""),
        })

    elif type_document == "rib":
        document_sortie.update({
            "company_name": document_json.get("company_name", ""),
            "siret": document_json.get("siret", ""),
            "bank_name": document_json.get("bank_name", ""),
            "iban": document_json.get("iban", ""),
            "bic": document_json.get("bic", ""),
            "account_holder": document_json.get("account_holder", ""),
        })

    # Si aucun vendor_id explicite n'est fourni, on réutilise la logique de construire_json :
    # priorité au SIRET (champs métier puis regex) puis au nom de l'entreprise, sinon le document_id.
    if not vendor_id:
        siret = str(document_json.get("siret", "")).strip()
        company_name = str(document_json.get("company_name", "")).strip()
        if not siret:
            champs_admin = document_json.get("champs_admin", {})
            sirets_admin = champs_admin.get("siret", []) if isinstance(champs_admin, dict) else []
            if sirets_admin:
                siret = str(sirets_admin[0]).strip()
        if siret:
            vendor_id = siret
        elif company_name:
            vendor_id = company_name
        else:
            vendor_id = document_json.get("document_id", "")

    return {
        "vendor_id": vendor_id,
        "documents": [document_sortie],
    }