from __future__ import annotations

from pathlib import Path
from typing import Any


def normalize_single_ocr_document(
    raw_doc: dict[str, Any],
    vendor_id: str,
    document_id: str | None = None,
) -> dict[str, Any]:
    """
    Transforme un document OCR brut ou semi-normalisé
    en document compatible avec le moteur.
    """

    document_type = raw_doc.get("document_type") or raw_doc.get("documentType")
    ocr_confidence = raw_doc.get("ocr_confidence") or raw_doc.get("ocrConfidence")

    # Si le document est déjà au format BDD/moteur
    if "extractedData" in raw_doc and isinstance(raw_doc.get("extractedData"), dict):
        return {
            "_id": raw_doc.get("_id") or raw_doc.get("documentId") or document_id,
            "vendorId": raw_doc.get("vendorId") or raw_doc.get("vendor_id") or vendor_id,
            "documentType": raw_doc.get("documentType") or raw_doc.get("document_type"),
            "ocrConfidence": raw_doc.get("ocrConfidence") or raw_doc.get("ocr_confidence"),
            "extractedData": raw_doc.get("extractedData", {}),
        }

    # Cas OCR brut : tous les champs métier sont au niveau racine
    extracted_data = {
        key: value
        for key, value in raw_doc.items()
        if key not in {
            "_id",
            "vendorId",
            "vendor_id",
            "documentId",
            "document_type",
            "documentType",
            "ocr_confidence",
            "ocrConfidence",
            "validation",
            "cleanDocumentId",
            "createdAt",
            "updatedAt",
        }
    }

    return {
        "_id": raw_doc.get("_id") or raw_doc.get("documentId") or document_id,
        "vendorId": raw_doc.get("vendorId") or raw_doc.get("vendor_id") or vendor_id,
        "documentType": document_type,
        "ocrConfidence": ocr_confidence,
        "extractedData": extracted_data,
    }


def normalize_ocr_vendor_data(
    raw_vendor_data: dict[str, Any],
    source_name: str | None = None,
) -> dict[str, Any]:
    """
    Transforme un payload fournisseur OCR brut en format moteur :
    {
      "vendorId": "...",
      "documents": [...]
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

        existing_id = (
            raw_doc.get("_id")
            or raw_doc.get("documentId")
            or raw_doc.get("cleanDocumentId")
        )

        fallback_id = f"{vendor_id}_{document_type}_{index}"
        if source_name and not existing_id:
            fallback_id = f"{Path(source_name).stem}_{index}"

        normalized_documents.append(
            normalize_single_ocr_document(
                raw_doc=raw_doc,
                vendor_id=vendor_id,
                document_id=existing_id or fallback_id,
            )
        )

    return {
        "vendorId": vendor_id,
        "documents": normalized_documents,
    }


def normalize_single_document_payload(
    payload: dict[str, Any],
    source_name: str | None = None,
) -> dict[str, Any]:
    """
    Transforme un document unique (ex: export BDD curateddocuments)
    en payload fournisseur compatible moteur.
    """
    vendor_id = payload.get("vendorId") or payload.get("vendor_id")
    if not vendor_id:
        raise ValueError("vendorId / vendor_id manquant dans le document unitaire.")

    document_type = payload.get("documentType") or payload.get("document_type") or "unknown"

    existing_id = (
        payload.get("_id")
        or payload.get("documentId")
        or payload.get("cleanDocumentId")
    )

    fallback_id = f"{vendor_id}_{document_type}_1"
    if source_name and not existing_id:
        fallback_id = Path(source_name).stem

    normalized_doc = normalize_single_ocr_document(
        raw_doc=payload,
        vendor_id=vendor_id,
        document_id=existing_id or fallback_id,
    )

    return {
        "vendorId": vendor_id,
        "documents": [normalized_doc],
    }


def is_ocr_raw_vendor_format(payload: dict[str, Any]) -> bool:
    """
    Détecte le format OCR brut de type :
    {
      "vendor_id": "...",
      "documents": [...]
    }
    """
    if not isinstance(payload, dict):
        return False

    if "documents" not in payload:
        return False

    documents = payload.get("documents")
    if not isinstance(documents, list):
        return False

    if not documents:
        return "vendor_id" in payload or "vendorId" in payload

    first_doc = documents[0]
    if not isinstance(first_doc, dict):
        return False

    return (
        "document_type" in first_doc
        or "ocr_confidence" in first_doc
        or "vendor_id" in payload
    )


def is_detector_vendor_format(payload: dict[str, Any]) -> bool:
    """
    Détecte si le payload est déjà au format moteur :
    {
      "vendorId": "...",
      "documents": [...]
    }
    """
    if not isinstance(payload, dict):
        return False

    if "vendorId" not in payload or "documents" not in payload:
        return False

    documents = payload.get("documents")
    return isinstance(documents, list)


def is_single_document_format(payload: dict[str, Any]) -> bool:
    """
    Détecte un document unitaire venant d'une BDD ou d'un export.
    """
    if not isinstance(payload, dict):
        return False

    has_vendor = "vendorId" in payload or "vendor_id" in payload
    has_doc_type = "documentType" in payload or "document_type" in payload
    has_extracted = "extractedData" in payload or has_doc_type

    return has_vendor and has_extracted and "documents" not in payload


def ensure_detector_input_format(
    payload: dict[str, Any],
    source_name: str | None = None,
) -> dict[str, Any]:
    """
    Retourne toujours un payload compatible avec le moteur :
    {
      "vendorId": "...",
      "documents": [...]
    }
    """
    if is_ocr_raw_vendor_format(payload):
        return normalize_ocr_vendor_data(payload, source_name=source_name)

    if is_single_document_format(payload):
        return normalize_single_document_payload(payload, source_name=source_name)

    if is_detector_vendor_format(payload):
        return payload

    raise ValueError("Format de payload non supporté.")