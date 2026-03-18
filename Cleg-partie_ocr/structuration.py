# structuration.py

"""
structuration.py
Construit le JSON final standardisé à partir de tous les éléments extraits
C'est ce JSON qui sera envoyé au Data Lake / pipeline Airflow
"""

import os
import hashlib
from datetime import datetime


def calc_hash(chemin_fichier: str) -> str:
    """
    Calcule le hash MD5 du fichier source (utile pour déduplication dans le Data Lake)
    """
    hasher = hashlib.md5()
    with open(chemin_fichier, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def _base_champs_par_type(type_document: str) -> dict:
    """
    Retourne la structure minimale attendue selon le type de document
    """
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
            "bank_name": "",
            "iban": "",
            "bic": "",
            "account_holder": "",
        },
    }
    return mapping.get(type_document, {})


def _extraire_confiance_ocr(taux_erreur: dict = None):
    """
    Retourne un score OCR simple exploitable par les modules aval
    """
    if not taux_erreur:
        return ""

    if "confiance_estimee_pct" in taux_erreur:
        return taux_erreur["confiance_estimee_pct"]

    if "cer_pct" in taux_erreur:
        return round(max(0.0, 100.0 - float(taux_erreur["cer_pct"])), 2)

    return ""


def _normaliser_score_confiance(ocr_confidence):
    """
    Normalise le score OCR entre 0 et 1 si besoin
    """
    if ocr_confidence in ("", None):
        return ""

    try:
        score = float(ocr_confidence)
    except (TypeError, ValueError):
        return ""

    if 0 <= score <= 1:
        return round(score, 4)

    if 0 <= score <= 100:
        return round(score / 100, 4)

    return ""


def construire_json(
    chemin_fichier: str,
    texte_brut: str,
    texte_propre: str,
    entites: dict,
    taux_erreur: dict = None
) -> dict:
    """
    Assemble le JSON final normalisé
    chemin_fichier : fichier source traité
    texte_brut     : texte sorti directement de l'OCR
    texte_propre   : texte après nettoyage
    entites        : dict retourné par extraire_entites()
    taux_erreur    : dict retourné par calc_taux_erreur() (None si pas calculé)
    Retourne le dict JSON complet
    """
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

    # Ajout des champs métier attendus selon le type
    base_champs = _base_champs_par_type(type_document)
    base_champs.update(champs_metier)
    resultat.update(base_champs)

    # Calcul d'un vendor_id stable :
    # 1. SIRET si disponible
    # 2. Sinon nom d'entreprise
    # 3. Sinon hash du fichier (unique)
    siret = str(resultat.get("siret", "")).strip()
    company_name = str(resultat.get("company_name", "")).strip()

    # Si les champs métier n'ont pas rempli le SIRET,
    # on tente de le récupérer depuis les champs admin regex.
    if not siret:
        champs_admin_sirets = resultat.get("champs_admin", {}).get("siret", [])
        if champs_admin_sirets:
            siret = str(champs_admin_sirets[0]).strip()
    if siret:
        resultat["vendor_id"] = siret
    elif company_name:
        resultat["vendor_id"] = company_name
    else:
        resultat["vendor_id"] = hash_md5

    # On conserve aussi les informations techniques utiles pour debug / traçabilité
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
    """
    Construit le payload attendu par le module anomalie :
    {
      "vendor_id": "...",
      "documents": [{...}]
    }
    """
    type_document = document_json.get("document_type", "unknown")

    document_sortie = {
        "document_type": type_document,
        "ocr_confidence": _normaliser_score_confiance(
            document_json.get("ocr_confidence", "")
        ),
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
        "documents": [document_sortie]
    }