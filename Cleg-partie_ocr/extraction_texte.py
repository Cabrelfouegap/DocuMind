"""
extraction_texte.py
Lit un fichier (image ou PDF) et retourne le texte brut via EasyOCR
"""

import easyocr
import fitz  # PyMuPDF — pour convertir PDF en images
import numpy as np
from PIL import Image
import io

# Lecteur EasyOCR (chargé une seule fois pour éviter de recharger le modèle)
_lecteur = None


def get_lecteur():
    """
    Initialise le lecteur EasyOCR une seule fois (français + anglais)
    """
    global _lecteur
    if _lecteur is None:
        # fr = français, en = anglais — ajouter d'autres langues si besoin
        _lecteur = easyocr.Reader(["fr", "en"], gpu=False)
    return _lecteur


def lire_image(chemin_img: str) -> str:
    """
    Lance l'OCR sur une image et retourne le texte brut
    chemin_img : chemin vers l'image (jpg, png, etc.)
    """
    lecteur = get_lecteur()
    resultats = lecteur.readtext(chemin_img, detail=0, paragraph=True)
    # detail=0 → retourne juste le texte, paragraph=True → regroupe par blocs
    return "\n".join(resultats)


def pdf_vers_images(chemin_pdf: str) -> list:
    """
    Convertit chaque page d'un PDF en image numpy (pour EasyOCR)
    Retourne une liste d'images numpy
    """
    doc = fitz.open(chemin_pdf)
    images = []
    for page in doc:
        # Résolution 300 DPI — bon compromis qualité/vitesse
        matrice = fitz.Matrix(300 / 72, 300 / 72)
        pix = page.get_pixmap(matrix=matrice)
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))
        images.append(np.array(img))
    doc.close()
    return images


def lire_pdf(chemin_pdf: str) -> str:
    """
    Tente d'abord d'extraire le texte natif du PDF (si dispo)
    Si échec ou vide → OCR sur images des pages
    """
    doc = fitz.open(chemin_pdf)
    textes = []

    for page in doc:
        texte_natif = page.get_text().strip()
        textes.append(texte_natif)

    doc.close()
    texte_complet = "\n".join(textes).strip()

    # Si le PDF est un scan (pas de texte natif), on fait OCR
    if len(texte_complet) < 50:
        print("[OCR] PDF scanné détecté → passage en mode OCR image")
        images = pdf_vers_images(chemin_pdf)
        lecteur = get_lecteur()
        textes_ocr = []
        for i, img in enumerate(images):
            print(f"[OCR] Page {i+1}/{len(images)}...")
            resultats = lecteur.readtext(img, detail=0, paragraph=True)
            textes_ocr.append("\n".join(resultats))
        return "\n\n--- PAGE SUIVANTE ---\n\n".join(textes_ocr)

    return texte_complet


def extraire_texte(chemin_fichier: str) -> str:
    """
    Point d'entrée unique : détecte si c'est un PDF ou une image
    et appelle la bonne fonction d'extraction
    """
    ext = chemin_fichier.lower().split(".")[-1]

    if ext == "pdf":
        return lire_pdf(chemin_fichier)
    elif ext in ("png", "jpg", "jpeg", "tiff", "bmp", "webp"):
        return lire_image(chemin_fichier)
    else:
        raise ValueError(f"Format non supporté : {ext}")
