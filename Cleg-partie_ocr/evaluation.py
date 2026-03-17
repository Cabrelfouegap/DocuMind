"""
evaluation.py
Calcul du taux d'erreur OCR (CER = Character Error Rate, WER = Word Error Rate)
CER = nb caractères mal reconnus / nb caractères total dans le texte de référence
WER = nb mots mal reconnus / nb mots total dans le texte de référence
"""

import re


def calc_distance_levenshtein(s1: str, s2: str) -> int:
    """
    Calcule la distance de Levenshtein entre deux chaînes
    (nombre minimal d'éditions pour passer de s1 à s2)
    """
    if len(s1) < len(s2):
        return calc_distance_levenshtein(s2, s1)

    if len(s2) == 0:
        return len(s1)

    ligne_prec = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        ligne_courante = [i + 1]
        for j, c2 in enumerate(s2):
            insertion   = ligne_prec[j + 1] + 1
            suppression = ligne_courante[j] + 1
            substitution = ligne_prec[j] + (c1 != c2)
            ligne_courante.append(min(insertion, suppression, substitution))
        ligne_prec = ligne_courante

    return ligne_prec[-1]


def calc_cer(texte_ocr: str, texte_ref: str) -> float:
    """
    Calcule le Character Error Rate (CER) en %
    texte_ocr : texte sorti de l'OCR
    texte_ref : texte de référence correct
    Retourne un float entre 0 et 100
    """
    if len(texte_ref) == 0:
        return 0.0
    dist = calc_distance_levenshtein(texte_ocr, texte_ref)
    cer = (dist / len(texte_ref)) * 100
    return round(min(cer, 100.0), 2)  # plafond à 100%


def calc_wer(texte_ocr: str, texte_ref: str) -> float:
    """
    Calcule le Word Error Rate (WER) en %
    Même logique que CER mais sur les mots
    """
    mots_ocr = re.findall(r"\S+", texte_ocr)
    mots_ref = re.findall(r"\S+", texte_ref)

    if len(mots_ref) == 0:
        return 0.0

    # Distance Levenshtein sur les séquences de mots
    dist = calc_distance_levenshtein(mots_ocr, mots_ref)
    wer = (dist / len(mots_ref)) * 100
    return round(min(wer, 100.0), 2)


def estimer_confiance(texte_ocr: str) -> float:
    """
    Estime la confiance OCR sans texte de référence
    Heuristique : ratio de caractères "propres" (alphanumériques + ponctuation courante)
    sur le total des caractères
    Retourne un score entre 0 et 100
    """
    if len(texte_ocr) == 0:
        return 0.0

    # Caractères considérés comme "valides"
    nb_valides = len(re.findall(r"[\w\s\.,;:!?()\-/€%@]", texte_ocr))
    score = (nb_valides / len(texte_ocr)) * 100
    return round(score, 2)


def calc_taux_erreur(texte_ocr: str, texte_ref: str = None) -> dict:
    """
    Calcule les métriques OCR disponibles selon si on a un texte de référence
    Si texte_ref fourni → CER + WER
    Sinon → estimation par heuristique
    Retourne un dict de métriques
    """
    if texte_ref:
        return {
            "cer_pct": calc_cer(texte_ocr, texte_ref),
            "wer_pct": calc_wer(texte_ocr, texte_ref),
            "mode": "avec_reference"
        }
    else:
        return {
            "confiance_estimee_pct": estimer_confiance(texte_ocr),
            "mode": "estimation_heuristique"
        }
