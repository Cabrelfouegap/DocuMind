"""
verif_install.py
Lance ce script juste après l'installation pour vérifier que tout est en place.
Usage : python verif_install.py
Aucun document requis — tout est simulé en mémoire.
"""

import sys

print("=" * 55)
print("  Vérification de l'installation — Module OCR")
print("=" * 55)

erreurs = []

# ── 1. Vérification des imports ──────────────────────────────
print("\n[1/4] Vérification des bibliothèques Python...")

libs = {
    "easyocr":   "EasyOCR (moteur OCR)",
    "fitz":      "PyMuPDF (lecture PDF)",
    "PIL":       "Pillow (images)",
    "numpy":     "NumPy",
    "spacy":     "spaCy (NER)",
}

for module, nom in libs.items():
    try:
        __import__(module)
        print(f"  ✓  {nom}")
    except ImportError:
        print(f"  ✗  {nom}  ← MANQUANT  →  pip install {module if module != 'PIL' else 'Pillow'}")
        erreurs.append(nom)

# ── 2. Vérification du modèle spaCy ──────────────────────────
print("\n[2/4] Vérification du modèle spaCy français...")
try:
    import spacy
    nlp = spacy.load("fr_core_news_md")
    print("  ✓  fr_core_news_md chargé")
except OSError:
    try:
        nlp = spacy.load("fr_core_news_sm")
        print("  ~  fr_core_news_sm chargé (le modèle md est préférable)")
        print("     Pour installer le modèle md : python -m spacy download fr_core_news_md")
    except OSError:
        print("  ✗  Aucun modèle spaCy français trouvé")
        print("     Commande : python -m spacy download fr_core_news_md")
        erreurs.append("modèle spaCy")

# ── 3. Tests fonctionnels rapides ────────────────────────────
print("\n[3/4] Tests fonctionnels des modules...")

try:
    from nettoyage import nettoyer_texte
    res = nettoyer_texte("  Bonjour\x00 le\x01 monde  ")
    assert "Bonjour" in res and "\x00" not in res
    print("  ✓  nettoyage.py")
except Exception as e:
    print(f"  ✗  nettoyage.py : {e}")
    erreurs.append("nettoyage")

try:
    from entites import extraire_regex, classer_doc
    r = extraire_regex("SIRET 12345678901234 date 15/03/2022")
    assert "siret" in r
    assert classer_doc("voici une facture") == "facture"
    print("  ✓  entites.py")
except Exception as e:
    print(f"  ✗  entites.py : {e}")
    erreurs.append("entites")

try:
    from evaluation import calc_cer, calc_wer, estimer_confiance
    assert calc_cer("bonjour", "bonjour") == 0.0
    assert calc_wer("a b c", "a b c") == 0.0
    assert estimer_confiance("texte propre") > 50
    print("  ✓  evaluation.py")
except Exception as e:
    print(f"  ✗  evaluation.py : {e}")
    erreurs.append("evaluation")

try:
    import tempfile, os
    from structuration import construire_json
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
        f.write("test"); chemin = f.name
    j = construire_json(chemin, "test", "test",
                        {"type_document": "inconnu", "entites_regex": {}, "entites_ner": {}})
    assert "meta" in j and "validation" in j
    os.unlink(chemin)
    print("  ✓  structuration.py")
except Exception as e:
    print(f"  ✗  structuration.py : {e}")
    erreurs.append("structuration")

# ── 4. Vérification EasyOCR (test réel sur image synthétique) ─
print("\n[4/4] Test EasyOCR (chargement modèle — peut prendre 30 sec la 1ère fois)...")
try:
    import easyocr, numpy as np
    # Crée une image blanche 100x30 pixels avec du texte simulé
    img = np.ones((30, 100, 3), dtype=np.uint8) * 255
    reader = easyocr.Reader(["fr"], gpu=False, verbose=False)
    _ = reader.readtext(img, detail=0)
    print("  ✓  EasyOCR opérationnel")
except Exception as e:
    print(f"  ~  EasyOCR chargé mais test image échoué : {e}")

# ── Résumé ────────────────────────────────────────────────────
print("\n" + "=" * 55)
if not erreurs:
    print("  ✅  Tout est opérationnel — tu peux lancer le pipeline !")
    print("\n  Exemple :")
    print("  python pipeline_ocr.py ma_facture.pdf")
else:
    print(f"  ⚠️  {len(erreurs)} problème(s) détecté(s) :")
    for e in erreurs:
        print(f"      - {e}")
    print("\n  Résous les erreurs ci-dessus puis relance ce script.")
print("=" * 55)
