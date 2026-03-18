from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from adapter import ensure_detector_input_format
from engine import RuleBasedAnomalyDetector


def load_json_file(file_path: Path) -> dict[str, Any]:
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(f"{file_path.name} ne contient pas un objet JSON valide.")

    return data


def save_json(data: Any, output_file: Path) -> None:
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def merge_vendor_payloads(input_dir: Path) -> list[dict[str, Any]]:
    """
    Lit tous les fichiers JSON OCR du dossier, les normalise,
    puis fusionne les documents par vendorId.
    """
    merged_vendors: dict[str, dict[str, Any]] = {}

    for file_path in sorted(input_dir.glob("*.json")):
        raw_payload = load_json_file(file_path)

        normalized_payload = ensure_detector_input_format(
            raw_payload,
            source_name=file_path.name,
        )

        vendor_id = normalized_payload.get("vendorId")
        documents = normalized_payload.get("documents", [])

        if not vendor_id:
            print(f"[WARNING] vendorId introuvable dans {file_path.name}, fichier ignoré.")
            continue

        if vendor_id not in merged_vendors:
            merged_vendors[vendor_id] = {
                "vendorId": vendor_id,
                "documents": [],
            }

        merged_vendors[vendor_id]["documents"].extend(documents)

    return list(merged_vendors.values())


def process_directory(
    input_dir: Path,
    detector: RuleBasedAnomalyDetector | None = None,
) -> list[dict[str, Any]]:
    """
    Traite un dossier complet de résultats OCR et retourne
    les résultats de détection d’anomalies par vendor.
    """
    detector = detector or RuleBasedAnomalyDetector()

    vendor_payloads = merge_vendor_payloads(input_dir)

    results = []
    for vendor_payload in vendor_payloads:
        result = detector.detect(vendor_payload)
        results.append(result)

    return results