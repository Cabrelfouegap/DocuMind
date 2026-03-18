from __future__ import annotations

from pathlib import Path
from typing import Any


def normalize_single_ocr_document(
    raw_doc: dict[str, Any],
    vendor_id: str,
    document_id: str | None = None,
) -> dict[str, Any]:
    """
    Transforme un document OCR brut en document compatible avec le moteur.
    """

    document_type = raw_doc.get("document_type") or raw_doc.get("documentType")
    ocr_confidence = raw_doc.get("ocr_confidence") or raw_doc.get("ocrConfidence")

    extracted_data = {
        key: value
        for key, value in raw_doc.items()
        if key not in {"document_type", "documentType", "ocr_confidence", "ocrConfidence"}
    }

    return {
        "_id": document_id,
        "vendorId": vendor_id,
        "documentType": document_type,
        "ocrConfidence": ocr_confidence,
        "extractedData": extracted_data,
    }


def normalize_ocr_vendor_data(
    raw_vendor_data: dict[str, Any],
    source_name: str | None = None,
) -> dict[str, Any]:
    """
    Transforme un JSON OCR brut de type :
    {
      "vendor_id": "V01",
      "documents": [
        {
          "document_type": "invoice",
          "ocr_confidence": 1.0,
          ...
        }
      ]
    }

    vers le format attendu par le moteur :
    {
      "vendorId": "V01",
      "documents": [
        {
          "_id": "...",
          "vendorId": "V01",
          "documentType": "invoice",
          "ocrConfidence": 1.0,
          "extractedData": {...}
        }
      ]
    }
    """

    if not isinstance(raw_vendor_data, dict):
        raise ValueError("Le payload fournisseur doit être un dictionnaire.")

    vendor_id = raw_vendor_data.get("vendor_id") or raw_vendor_data.get("vendorId")
    if not vendor_id:
        raise ValueError("vendor_id / vendorId manquant dans le payload OCR.")

    raw_documents = raw_vendor_data.get("documents", [])
    if not isinstance(raw_documents, list):
        raise ValueError("Le champ 'documents' doit être une liste.")

    normalized_documents = []

    for index, raw_doc in enumerate(raw_documents, start=1):
        if not isinstance(raw_doc, dict):
            continue

        document_type = raw_doc.get("document_type") or raw_doc.get("documentType") or "unknown"
        document_id = f"{vendor_id}_{document_type}_{index}"

        if source_name:
            document_id = f"{Path(source_name).stem}_{index}"

        normalized_documents.append(
            normalize_single_ocr_document(
                raw_doc=raw_doc,
                vendor_id=vendor_id,
                document_id=document_id,
            )
        )

    return {
        "vendorId": vendor_id,
        "documents": normalized_documents,
    }


def is_ocr_raw_vendor_format(payload: dict[str, Any]) -> bool:
    """
    Détecte si le payload ressemble au format OCR brut.
    """
    if not isinstance(payload, dict):
        return False

    if "documents" not in payload:
        return False

    documents = payload.get("documents")
    if not isinstance(documents, list) or not documents:
        return "vendor_id" in payload or "vendorId" in payload

    first_doc = documents[0]
    if not isinstance(first_doc, dict):
        return False

    return (
        "document_type" in first_doc
        or "ocr_confidence" in first_doc
        or "vendor_id" in payload
    )


def ensure_detector_input_format(
    payload: dict[str, Any],
    source_name: str | None = None,
) -> dict[str, Any]:
    """
    Retourne toujours un payload compatible avec le moteur.
    """
    if is_ocr_raw_vendor_format(payload):
        return normalize_ocr_vendor_data(payload, source_name=source_name)

    return payload