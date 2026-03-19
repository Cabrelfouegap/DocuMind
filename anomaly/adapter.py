from __future__ import annotations

from pathlib import Path
from typing import Any



TECHNICAL_FIELDS = {
    "_id",
    "vendorId",
    "vendor_id",
    "documentId",
    "documentType",
    "document_type",
    "ocrConfidence",
    "ocr_confidence",
    "validation",
    "cleanDocumentId",
    "createdAt",
    "updatedAt",
}


def _get_vendor_id(payload: dict[str, Any]) -> str | None:
    return payload.get("vendorId") or payload.get("vendor_id")


def _get_document_type(payload: dict[str, Any]) -> str | None:
    return payload.get("documentType") or payload.get("document_type")


def _get_ocr_confidence(payload: dict[str, Any]) -> Any:
    return payload.get("ocrConfidence") or payload.get("ocr_confidence")


def _get_document_id(payload: dict[str, Any]) -> Any:
    return (
        payload.get("_id")
        or payload.get("documentId")
        or payload.get("cleanDocumentId")
    )


def _build_fallback_document_id(
    vendor_id: str,
    document_type: str,
    index: int = 1,
    source_name: str | None = None,
) -> str:
    if source_name:
        return f"{Path(source_name).stem}_{index}"
    return f"{vendor_id}_{document_type}_{index}"


def normalize_single_document(
    raw_doc: dict[str, Any],
    vendor_id: str,
    document_id: str | None = None,
) -> dict[str, Any]:
    """
    Transforme un document brut, semi-normalisé ou issu de la BDD
    en document compatible avec le moteur.
    """

    document_type = _get_document_type(raw_doc)
    ocr_confidence = _get_ocr_confidence(raw_doc)
    resolved_document_id = _get_document_id(raw_doc) or document_id
    resolved_vendor_id = _get_vendor_id(raw_doc) or vendor_id

    # Cas 1 : document déjà proche du format moteur / BDD
    if isinstance(raw_doc.get("extractedData"), dict):
        return {
            "_id": resolved_document_id,
            "vendorId": resolved_vendor_id,
            "documentType": document_type,
            "ocrConfidence": ocr_confidence,
            "extractedData": raw_doc.get("extractedData", {}),
        }

    # Cas 2 : document brut OCR
    extracted_data = {
        key: value
        for key, value in raw_doc.items()
        if key not in TECHNICAL_FIELDS
    }

    return {
        "_id": resolved_document_id,
        "vendorId": resolved_vendor_id,
        "documentType": document_type,
        "ocrConfidence": ocr_confidence,
        "extractedData": extracted_data,
    }


def normalize_raw_vendor_payload(
    raw_vendor_payload: dict[str, Any],
    source_name: str | None = None,
) -> dict[str, Any]:
    """
    Transforme un payload fournisseur brut ou semi-structuré
    en format compatible avec le moteur :

    {
      "vendorId": "...",
      "documents": [...]
    }
    """
    if not isinstance(raw_vendor_payload, dict):
        raise ValueError("Le payload fournisseur doit être un dictionnaire.")

    vendor_id = _get_vendor_id(raw_vendor_payload)
    if not vendor_id:
        raise ValueError("vendor_id / vendorId manquant dans le payload fournisseur.")

    raw_documents = raw_vendor_payload.get("documents", [])
    if not isinstance(raw_documents, list):
        raise ValueError("Le champ 'documents' doit être une liste.")

    normalized_documents: list[dict[str, Any]] = []

    for index, raw_doc in enumerate(raw_documents, start=1):
        if not isinstance(raw_doc, dict):
            continue

        document_type = _get_document_type(raw_doc) or "unknown"
        document_id = _get_document_id(raw_doc) or _build_fallback_document_id(
            vendor_id=vendor_id,
            document_type=document_type,
            index=index,
            source_name=source_name,
        )

        normalized_documents.append(
            normalize_single_document(
                raw_doc=raw_doc,
                vendor_id=vendor_id,
                document_id=document_id,
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
    Transforme un document unitaire 
    en payload fournisseur compatible moteur.
    """
    if not isinstance(payload, dict):
        raise ValueError("Le document unitaire doit être un dictionnaire.")

    vendor_id = _get_vendor_id(payload)
    if not vendor_id:
        raise ValueError("vendorId / vendor_id manquant dans le document unitaire.")

    document_type = _get_document_type(payload) or "unknown"
    document_id = _get_document_id(payload) or _build_fallback_document_id(
        vendor_id=vendor_id,
        document_type=document_type,
        index=1,
        source_name=source_name,
    )

    normalized_doc = normalize_single_document(
        raw_doc=payload,
        vendor_id=vendor_id,
        document_id=document_id,
    )

    return {
        "vendorId": vendor_id,
        "documents": [normalized_doc],
    }


def is_raw_vendor_payload(payload: dict[str, Any]) -> bool:
    """
    Détecte un payload fournisseur contenant plusieurs documents :
    {
      "vendor_id" ou "vendorId": "...",
      "documents": [...]
    }
    """
    if not isinstance(payload, dict):
        return False

    documents = payload.get("documents")
    if not isinstance(documents, list):
        return False

    return "vendor_id" in payload or "vendorId" in payload


def is_single_document_payload(payload: dict[str, Any]) -> bool:
    """
    Détecte un document unitaire venant d'une BDD, d'un export ou d'un OCR structuré.
    """
    if not isinstance(payload, dict):
        return False

    has_vendor = "vendorId" in payload or "vendor_id" in payload
    has_document_type = "documentType" in payload or "document_type" in payload
    has_extracted_data = "extractedData" in payload

    return has_vendor and (has_document_type or has_extracted_data) and "documents" not in payload


def is_detector_payload(payload: dict[str, Any]) -> bool:
    """
    Détecte si le payload est déjà au format attendu par le moteur :
    {
      "vendorId": "...",
      "documents": [...]
    }
    """
    if not isinstance(payload, dict):
        return False

    return "vendorId" in payload and isinstance(payload.get("documents"), list)


def ensure_detector_input_format(
    payload: dict[str, Any],
    source_name: str | None = None,
) -> dict[str, Any]:

    if is_detector_payload(payload):
        return payload

    if is_raw_vendor_payload(payload):
        return normalize_raw_vendor_payload(payload, source_name=source_name)

    if is_single_document_payload(payload):
        return normalize_single_document_payload(payload, source_name=source_name)

    raise ValueError("Format de payload non supporté.")