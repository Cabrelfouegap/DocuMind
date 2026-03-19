from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from adapter import ensure_detector_input_format
from engine import RuleBasedAnomalyDetector


def load_json_file(file_path: Path) -> dict[str, Any]:
    """
    Charge un fichier JSON et vérifie que son contenu
    est bien un objet JSON.
    """
    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(f"{file_path.name} ne contient pas un objet JSON valide.")

    return data


def save_json(data: Any, output_file: Path) -> None:
    """
    Sauvegarde des données Python au format JSON.
    """
    with output_file.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def merge_vendor_payloads(input_dir: Path) -> list[dict[str, Any]]:
    """
    Lit tous les fichiers JSON d'un dossier, normalise leur structure,
    puis fusionne les documents par fournisseur.
    """
    merged_by_vendor: dict[str, dict[str, Any]] = {}

    for file_path in sorted(input_dir.glob("*.json")):
        try:
            raw_payload = load_json_file(file_path)
            normalized_payload = ensure_detector_input_format(
                payload=raw_payload,
                source_name=file_path.name,
            )
        except Exception as error:
            print(f"[WARNING] Fichier ignoré ({file_path.name}) : {error}")
            continue

        vendor_id = normalized_payload.get("vendorId")
        documents = normalized_payload.get("documents", [])

        if not vendor_id:
            print(f"[WARNING] vendorId introuvable dans {file_path.name}, fichier ignoré.")
            continue

        if vendor_id not in merged_by_vendor:
            merged_by_vendor[vendor_id] = {
                "vendorId": vendor_id,
                "documents": [],
            }

        merged_by_vendor[vendor_id]["documents"].extend(documents)

    return list(merged_by_vendor.values())


def process_directory(
    input_dir: Path,
    detector: RuleBasedAnomalyDetector | None = None,
) -> list[dict[str, Any]]:
    """
    Traite tous les fichiers JSON d'un dossier :
    - normalisation des inputs
    - fusion par vendorId
    - détection d'anomalies pour chaque fournisseur
    """
    detector = detector or RuleBasedAnomalyDetector()
    vendor_payloads = merge_vendor_payloads(input_dir)

    results: list[dict[str, Any]] = []

    for vendor_payload in vendor_payloads:
        detection_result = detector.detect(vendor_payload)
        results.append(detection_result)

    return results