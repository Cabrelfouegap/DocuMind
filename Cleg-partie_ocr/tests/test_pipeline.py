"""
tests/test_pipeline.py
Tests unitaires et de bout en bout du module OCR
Lancement : python -m pytest tests/test_pipeline.py -v
"""

import os
import sys
import json
import tempfile

# Ajoute du dossier parent au path pour importer les modules

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nettoyage import (
    nettoyer_texte,
    suppr_caract_parasites,
    norm_espaces,
    corriger_ocr_classiques,
    norm_unicode,
)
from entites import extraire_regex, classer_doc, extraire_entites
from evaluation import calc_cer, calc_wer, estimer_confiance, calc_taux_erreur
from structuration import construire_json


# ════════════════════════════════════════════════════════════════════
# TESTS — nettoyage.py
# ════════════════════════════════════════════════════════════════════

def test_suppr_caract_parasites_basique():
    """Les caractères bizarres doivent être supprimés"""
    texte = "Bonjour\x00 le\x01 monde\x02"
    resultat = suppr_caract_parasites(texte)
    assert "\x00" not in resultat
    assert "\x01" not in resultat
    assert "Bonjour" in resultat


def test_norm_espaces_multiples():
    """Plusieurs espaces → un seul"""
    texte = "Bonjour    le     monde"
    resultat = norm_espaces(texte)
    assert "  " not in resultat
    assert "Bonjour le monde" == resultat


def test_norm_espaces_sauts_de_ligne():
    """Plus de 2 sauts de ligne → exactement 2"""
    texte = "Ligne 1\n\n\n\n\nLigne 2"
    resultat = norm_espaces(texte)
    assert "\n\n\n" not in resultat


def test_corriger_siret():
    """Le SIRET avec espaces parasites doit être recollé"""
    texte = "SIRET : 123 456 789 012 34"
    resultat = corriger_ocr_classiques(texte)
    assert "12345678901234" in resultat.replace(" ", "").replace("SIRET:", "")


def test_nettoyer_texte_pipeline_complet():
    """Le pipeline de nettoyage complet ne doit pas crasher"""
    texte_brut = "  Facture N°123\x00\n\n\n\nSIRET : 123 456 789 01234  "
    resultat = nettoyer_texte(texte_brut)
    assert isinstance(resultat, str)
    assert len(resultat) > 0
    assert "\x00" not in resultat


# ════════════════════════════════════════════════════════════════════
# TESTS — entites.py
# ════════════════════════════════════════════════════════════════════

def test_regex_siret_detecte():
    """Un SIRET de 14 chiffres doit être détecté"""
    texte = "Notre numéro SIRET est 12345678901234."
    resultat = extraire_regex(texte)
    assert "siret" in resultat
    assert "12345678901234" in resultat["siret"]


def test_regex_date_detectee():
    """Une date au format JJ/MM/AAAA doit être détectée"""
    texte = "Date d'émission : 15/03/2022"
    resultat = extraire_regex(texte)
    assert "date" in resultat
    assert any("15/03/2022" in d for d in resultat["date"])


def test_regex_email_detecte():
    """Un email doit être détecté"""
    texte = "Contactez-nous à contact@entreprise.fr pour toute question."
    resultat = extraire_regex(texte)
    assert "email" in resultat
    assert "contact@entreprise.fr" in resultat["email"]


def test_regex_montant_detecte():
    """Un montant en euros doit être détecté"""
    texte = "Total TTC : 1 250,00 €"
    resultat = extraire_regex(texte)
    assert "montant" in resultat


def test_regex_iban_detecte():
    """Un IBAN doit être détecté"""
    texte = "IBAN : FR76 3000 6000 0112 3456 7890 189"
    resultat = extraire_regex(texte)
    assert "iban" in resultat
    assert resultat["iban"][0].startswith("FR76")


def test_classer_doc_invoice():
    """Un texte contenant 'facture' doit être classé comme invoice"""
    assert classer_doc("Ceci est une FACTURE de prestation.") == "invoice"


def test_classer_doc_quote():
    """Un texte contenant 'devis' doit être classé comme quote"""
    assert classer_doc("DEVIS N°2022-001") == "quote"


def test_classer_doc_urssaf():
    """Une attestation de vigilance doit être classée comme urssaf"""
    assert classer_doc("Attestation de vigilance URSSAF valable jusqu'au 31/12/2026") == "urssaf"


def test_classer_doc_kbis():
    """Un extrait Kbis doit être classé comme kbis"""
    assert classer_doc("Extrait KBIS du registre du commerce") == "kbis"


def test_classer_doc_rib():
    """Un document avec IBAN/BIC doit être classé comme rib"""
    assert classer_doc("RELEVE D'IDENTITE BANCAIRE\nIBAN FR76...\nBIC AGRIFRPP") == "rib"


def test_classer_doc_unknown():
    """Un texte sans mot-clé connu → unknown"""
    assert classer_doc("Lorem ipsum dolor sit amet.") == "unknown"


def test_extraire_entites_retourne_structure_correcte():
    """La sortie doit contenir les clés attendues"""
    texte = "Facture émise par DUPONT SAS, SIRET 12345678901234."
    resultat = extraire_entites(texte)
    assert "type_document" in resultat
    assert "entites_regex" in resultat
    assert "entites_ner" in resultat
    assert "champs_metier" in resultat


def test_extraire_entites_invoice_champs_metier():
    """Une facture doit renvoyer les champs métier principaux"""
    texte = """
    FACTURE F-2026-001
    Société : DUPONT SAS
    SIRET 12345678901234
    Description : Prestation de conseil
    TVA 20%
    Total HT : 1000,00 €
    Total TTC : 1200,00 €
    Date : 15/03/2026
    """
    resultat = extraire_entites(texte)
    assert resultat["type_document"] == "invoice"
    assert "invoice_number" in resultat["champs_metier"]
    assert "total_ttc" in resultat["champs_metier"]


# ════════════════════════════════════════════════════════════════════
# TESTS — evaluation.py
# ════════════════════════════════════════════════════════════════════

def test_cer_textes_identiques():
    """CER entre deux textes identiques = 0%"""
    assert calc_cer("bonjour", "bonjour") == 0.0


def test_cer_textes_totalement_differents():
    """CER entre textes très différents doit être > 0"""
    assert calc_cer("aaaa", "bbbb") > 0


def test_wer_textes_identiques():
    """WER entre deux textes identiques = 0%"""
    assert calc_wer("bonjour le monde", "bonjour le monde") == 0.0


def test_wer_un_mot_different():
    """WER avec un mot différent sur 3 = environ 33%"""
    wer = calc_wer("bonjour le monde", "bonjour la monde")
    assert 0 < wer <= 50


def test_cer_reference_vide():
    """CER avec référence vide = 0 (pas de division par zéro)"""
    assert calc_cer("quelque chose", "") == 0.0


def test_estimer_confiance_texte_propre():
    """Un texte propre doit avoir une confiance élevée (> 80%)"""
    texte = "Bonjour, voici une facture pour les services rendus en mars 2022."
    assert estimer_confiance(texte) > 80.0


def test_estimer_confiance_texte_vide():
    """Un texte vide → confiance 0"""
    assert estimer_confiance("") == 0.0


def test_calc_taux_erreur_avec_reference():
    """Avec référence → doit retourner cer_pct et wer_pct"""
    resultat = calc_taux_erreur("bonjour monde", "bonjour le monde")
    assert "cer_pct" in resultat
    assert "wer_pct" in resultat
    assert resultat["mode"] == "avec_reference"


def test_calc_taux_erreur_sans_reference():
    """Sans référence → doit retourner confiance_estimee_pct"""
    resultat = calc_taux_erreur("bonjour le monde")
    assert "confiance_estimee_pct" in resultat
    assert resultat["mode"] == "estimation_heuristique"


# ════════════════════════════════════════════════════════════════════
# TESTS — structuration.py
# ════════════════════════════════════════════════════════════════════

def test_construire_json_structure_invoice():
    """Le JSON produit doit contenir les champs communs et métier d'une invoice"""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as f:
        f.write("Facture test SIRET 12345678901234")
        chemin = f.name

    try:
        entites = {
            "type_document": "invoice",
            "entites_regex": {"siret": ["12345678901234"]},
            "entites_ner": {"ORG": ["DUPONT SAS"]},
            "champs_metier": {
                "company_name": "DUPONT SAS",
                "siret": "12345678901234",
                "invoice_number": "F-2026-001",
                "product_description": "Prestation de conseil",
                "amount_ht": "1000,00 €",
                "vat_rate": "20%",
                "total_ttc": "1200,00 €",
                "invoice_issue_date": "15/03/2026",
            },
        }

        resultat = construire_json(
            chemin_fichier=chemin,
            texte_brut="Facture test",
            texte_propre="Facture test",
            entites=entites,
            taux_erreur={"confiance_estimee_pct": 95.0, "mode": "estimation_heuristique"}
        )

        assert resultat["document_id"] != ""
        assert resultat["vendor_id"] == ""
        assert resultat["file_name"] == os.path.basename(chemin)
        assert resultat["document_type"] == "invoice"
        assert resultat["ocr_confidence"] == 95.0

        assert resultat["company_name"] == "DUPONT SAS"
        assert resultat["invoice_number"] == "F-2026-001"
        assert resultat["total_ttc"] == "1200,00 €"

        assert "meta" in resultat
        assert "qualite_ocr" in resultat
        assert "validation" in resultat

        json_str = json.dumps(resultat, ensure_ascii=False)
        assert len(json_str) > 0

    finally:
        os.unlink(chemin)


def test_construire_json_rib_structure():
    """Le JSON RIB doit exposer les bons champs métier"""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as f:
        f.write("RIB test")
        chemin = f.name

    try:
        entites = {
            "type_document": "rib",
            "entites_regex": {
                "iban": ["FR7630006000011234567890189"],
                "bic": ["AGRIFRPP"],
            },
            "entites_ner": {"ORG": ["Crédit Agricole"]},
            "champs_metier": {
                "bank_name": "Crédit Agricole",
                "iban": "FR7630006000011234567890189",
                "bic": "AGRIFRPP",
                "account_holder": "DUPONT SAS",
            },
        }

        resultat = construire_json(
            chemin_fichier=chemin,
            texte_brut="RIB test",
            texte_propre="RIB test",
            entites=entites,
            taux_erreur={"confiance_estimee_pct": 88.0, "mode": "estimation_heuristique"}
        )

        assert resultat["document_type"] == "rib"
        assert resultat["bank_name"] == "Crédit Agricole"
        assert resultat["iban"] == "FR7630006000011234567890189"
        assert resultat["bic"] == "AGRIFRPP"
        assert resultat["account_holder"] == "DUPONT SAS"

    finally:
        os.unlink(chemin)