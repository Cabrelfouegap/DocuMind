"""
nettoyage.py
Nettoie le texte brut sorti de l'OCR (caractères parasites, espaces, etc.)
"""

import re
import unicodedata


def suppr_caract_parasites(texte: str) -> str:
    """
    Supprime les caractères non-imprimables et bizarre générés par l'OCR
    (boîtes, symboles inconnus, etc.)
    """
    # Garde lettres, chiffres, ponctuation courante et espaces/sauts de ligne
    texte = re.sub(r"[^\w\s\.,;:!?()\-/\\@#%€$£°\n]", " ", texte)
    return texte


def norm_espaces(texte: str) -> str:
    """
    Normalise les espaces multiples et les lignes vides en excès
    """
    # Plusieurs espaces → un seul
    texte = re.sub(r" {2,}", " ", texte)
    # Plus de 2 sauts de ligne d'affilée → 2 max
    texte = re.sub(r"\n{3,}", "\n\n", texte)
    return texte.strip()


def norm_unicode(texte: str) -> str:
    """
    Normalise l'encodage unicode (accents composés → décomposés puis recomposés)
    Évite les problèmes d'affichage d'accents
    """
    return unicodedata.normalize("NFC", texte)


def corriger_ocr_classiques(texte: str) -> str:
    """
    Corrige les erreurs OCR fréquentes sur documents administratifs français
    Ex : '0' confondu avec 'O', '1' avec 'l', etc.
    """
    corrections = {
        r"\bSIRET\s*:\s*(\d[\d\s]{13,})": lambda m: "SIRET: " + m.group(1).replace(" ", ""),
        r"\bSIREN\s*:\s*(\d[\d\s]{8,})": lambda m: "SIREN: " + m.group(1).replace(" ", ""),
        r"([€$£])\s+(\d)": r"\1\2",          # "€ 100" → "€100"
        r"(\d)\s+([.,])\s+(\d)": r"\1\2\3",  # "10 . 50" → "10.50"
    }
    for pattern, remplacement in corrections.items():
        texte = re.sub(pattern, remplacement, texte)
    return texte


def nettoyer_texte(texte_brut: str) -> str:
    """
    Pipeline de nettoyage complet — à appeler sur le texte brut OCR
    Retourne le texte propre
    """
    texte = norm_unicode(texte_brut)
    texte = suppr_caract_parasites(texte)
    texte = corriger_ocr_classiques(texte)
    texte = norm_espaces(texte)
    return texte
