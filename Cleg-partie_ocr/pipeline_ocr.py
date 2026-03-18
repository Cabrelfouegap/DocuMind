# pipeline_ocr.py
"""
Pipeline OCR principal
- extraction texte
- nettoyage
- extraction entités
- estimation qualité OCR
- structuration JSON
- payload métier pour anomalies
"""

import os
import sys
import json

from extraction_texte import extraire_texte
from nettoyage import nettoyer_texte
from entites import extraire_entites
from evaluation import calc_taux_erreur, estimer_confiance
from structuration import construire_json, construire_payload_vendor

DOSSIER_SORTIE = "resultats_ocr"
SAVE_DEBUG_JSON = False  # passe à True si vous voulez aussi les JSON debug


def _extraire_vendor_id_depuis_chemin(chemin_fichier: str) -> str:
    """
    Exemple :
    ..\\dataset\\dataset\\V03\\invoice.jpg -> V03
    """
    parent = os.path.basename(os.path.dirname(chemin_fichier))
    return parent.strip() if parent else ""


def traiter_doc(chemin_fichier: str) -> dict:
    print(f"[OCR] Traitement de : {chemin_fichier}")

    texte_brut = extraire_texte(chemin_fichier)
    texte_propre = nettoyer_texte(texte_brut)
    entites = extraire_entites(texte_propre)

    try:
        taux_err = calc_taux_erreur(texte_propre)
    except TypeError:
        # fallback si la fonction attend une référence et n'est pas fournie
        confiance = estimer_confiance(texte_propre)
        taux_err = {
            "confiance_estimee_pct": confiance,
            "mode": "estimation_heuristique",
        }
    except Exception:
        confiance = estimer_confiance(texte_propre)
        taux_err = {
            "confiance_estimee_pct": confiance,
            "mode": "estimation_heuristique",
        }

    resultat = construire_json(
        chemin_fichier=chemin_fichier,
        texte_brut=texte_brut,
        texte_propre=texte_propre,
        entites=entites,
        taux_erreur=taux_err,
    )

    vendor_id = _extraire_vendor_id_depuis_chemin(chemin_fichier)
    resultat["vendor_id"] = vendor_id

    payload_vendor = construire_payload_vendor(
        document_json=resultat,
        vendor_id=vendor_id,
    )

    os.makedirs(DOSSIER_SORTIE, exist_ok=True)

    parent = os.path.basename(os.path.dirname(chemin_fichier))
    nom_fichier = os.path.splitext(os.path.basename(chemin_fichier))[0]
    nom_base = f"{parent}_{nom_fichier}" if parent else nom_fichier

    chemin_json_metier = os.path.join(DOSSIER_SORTIE, f"{nom_base}.json")
    with open(chemin_json_metier, "w", encoding="utf-8") as f:
        json.dump(payload_vendor, f, ensure_ascii=False, indent=2)

    print(f"[OCR] JSON métier sauvegardé dans : {chemin_json_metier}")

    if SAVE_DEBUG_JSON:
        chemin_json_debug = os.path.join(DOSSIER_SORTIE, f"{nom_base}_debug.json")
        with open(chemin_json_debug, "w", encoding="utf-8") as f:
            json.dump(resultat, f, ensure_ascii=False, indent=2)
        print(f"[OCR] JSON debug sauvegardé dans : {chemin_json_debug}")

    return payload_vendor


def traiter_dossier(dossier: str) -> list:
    extensions_ok = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".pdf", ".webp"}
    resultats = []

    for nom in sorted(os.listdir(dossier)):
        chemin = os.path.join(dossier, nom)

        if not os.path.isfile(chemin):
            continue

        ext = os.path.splitext(nom)[1].lower()
        if ext not in extensions_ok:
            continue

        try:
            payload = traiter_doc(chemin)
            resultats.append(payload)
        except Exception as e:
            print(f"[ERREUR] {nom} : {e}")

    return resultats


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python pipeline_ocr.py <fichier_ou_dossier>")
        sys.exit(1)

    cible = sys.argv[1]

    if os.path.isdir(cible):
        traiter_dossier(cible)
    elif os.path.isfile(cible):
        traiter_doc(cible)
    else:
        print(f"Cible introuvable : {cible}")
        sys.exit(1)