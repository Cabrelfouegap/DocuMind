from __future__ import annotations

from pathlib import Path

from batch_processor import process_directory, save_json


INPUT_DIR = Path("sample_ocr_results")
OUTPUT_FILE = Path("anomaly_results.json")


def main() -> None:
    if not INPUT_DIR.exists():
        raise FileNotFoundError(f"Dossier introuvable : {INPUT_DIR.resolve()}")

    results = process_directory(INPUT_DIR)
    save_json(results, OUTPUT_FILE)

    print(f"Résultats sauvegardés dans : {OUTPUT_FILE.resolve()}")


if __name__ == "__main__":
    main()