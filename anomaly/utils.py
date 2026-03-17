from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

from rules import DATE_FORMATS


IBAN_REGEX = re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}$")
FLOAT_REGEX = re.compile(r"-?\d+(\.\d+)?")


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().lower().split())


def parse_date(date_str: Any) -> date | None:
    if not date_str:
        return None

    cleaned_date = str(date_str).strip()

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(cleaned_date, fmt).date()
        except ValueError:
            continue

    return None


def safe_float(value: Any) -> float | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    normalized_text = (
        text.lower()
        .replace("€", "")
        .replace("eur", "")
        .replace("ttc", "")
        .replace("ht", "")
        .replace(" ", "")
        .replace(",", ".")
    )

    match = FLOAT_REGEX.search(normalized_text)
    if not match:
        return None

    try:
        return float(match.group())
    except ValueError:
        return None


def is_valid_iban(iban: Any) -> bool:
    if not iban:
        return False

    cleaned_iban = str(iban).replace(" ", "").upper()
    return bool(IBAN_REGEX.match(cleaned_iban))


def get_extracted_data(doc: dict[str, Any]) -> dict[str, Any]:
    return doc.get("extractedData", {}) or {}


def get_field(doc: dict[str, Any], field_name: str, default: Any = None) -> Any:
    extracted_data = get_extracted_data(doc)
    return extracted_data.get(field_name, default)


def get_document_type(doc: dict[str, Any]) -> str | None:
    return doc.get("documentType")


def get_vendor_id_from_documents(documents: list[dict[str, Any]]) -> str | None:
    if not documents:
        return None
    return documents[0].get("vendorId")


def get_document_id(doc: dict[str, Any]) -> Any:
    return doc.get("_id")


def get_document(
    documents: list[dict[str, Any]],
    document_type: str,
) -> dict[str, Any] | None:
    return next(
        (doc for doc in documents if get_document_type(doc) == document_type),
        None,
    )


def get_documents(
    documents: list[dict[str, Any]],
    document_types: list[str],
) -> list[dict[str, Any]]:
    return [
        doc
        for doc in documents
        if get_document_type(doc) in document_types
    ]