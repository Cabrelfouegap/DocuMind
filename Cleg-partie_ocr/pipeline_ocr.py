# pipeline_ocr.py
"""
pipeline_ocr.py
Point d'entrée principal — traite un document et retourne un JSON structuré
"""

import json
import os

from extraction_texte import extraire_texte
from nettoyage import nettoyer_texte
from entites import extraire_entites
from evaluation import calc_taux_erreur
from structuration import construire_json, construire_payload_vendor

DOSSIER_SORTIE = "resultats_ocr"


def traiter_doc(chemin_fichier: str) -> dict:
    """
    Traite un document complet : OCR → nettoyage → entités → JSON
    chemin_fichier : chemin vers image ou PDF
    Retourne le dict JSON métier final
    """
    print(f"[OCR] Traitement de : {chemin_fichier}")

    # Étape 1 — Extraction brute du texte
    texte_brut = extraire_texte(chemin_fichier)

    # Étape 2 — Nettoyage du texte extrait
    texte_propre = nettoyer_texte(texte_brut)

    # Étape 3 — Extraction des entités et champs métier
    entites = extraire_entites(texte_propre)

    # Étape 4 — Évaluation qualité OCR
    taux_err = calc_taux_erreur(texte_propre)

    # Étape 5 — Structuration JSON complet
    resultat = construire_json(
        chemin_fichier=chemin_fichier,
        texte_brut=texte_brut,
        texte_propre=texte_propre,
        entites=entites,
        taux_erreur=taux_err
    )

    # Vendor = nom du dossier parent (ex : V01, V02, ...)
    parent = os.path.basename(os.path.dirname(chemin_fichier))

    # Payload métier pour l'anomaly detector
    payload_vendor = construire_payload_vendor(
        document_json=resultat,
        vendor_id=parent
    )

    # Sauvegarde (sur disque)
    
    os.makedirs(DOSSIER_SORTIE, exist_ok=True)

    parent = os.path.basename(os.path.dirname(chemin_fichier))
    nom_fichier = os.path.splitext(os.path.basename(chemin_fichier))[0]
    nom_base = f"{parent}_{nom_fichier}"

    chemin_json_metier = os.path.join(DOSSIER_SORTIE, f"{nom_base}.json")

    with open(chemin_json_metier, "w", encoding="utf-8") as f:
        json.dump(payload_vendor, f, ensure_ascii=False, indent=2)

    print(f"[OCR] JSON métier sauvegardé dans : {chemin_json_metier}")

    return payload_vendor


def traiter_dossier(dossier: str) -> list:
    """
    Traite tous les fichiers d'un dossier (images + PDFs)
    Retourne la liste des résultats JSON métier
    """
    extensions_ok = (".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".pdf", ".webp")
    resultats = []

    for fichier in os.listdir(dossier):
        if fichier.lower().endswith(extensions_ok):
            chemin = os.path.join(dossier, fichier)
            try:
                res = traiter_doc(chemin)
                resultats.append(res)
            except Exception as e:
                print(f"[ERREUR] {fichier} : {e}")

    return resultats


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage : python pipeline_ocr.py <chemin_fichier_ou_dossier>")
    else:
        cible = sys.argv[1]
        if os.path.isdir(cible):
            traiter_dossier(cible)
        else:
            traiter_doc(cible)