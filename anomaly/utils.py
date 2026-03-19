from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

from rules import DATE_FORMATS


IBAN_REGEX = re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}$")
FLOAT_REGEX = re.compile(r"-?\d+(\.\d+)?")


def normalize_text(value: Any) -> str:
    """
    - conversion en chaîne
    - suppression des espaces multiples
    - passage en minuscules
    """
    if value is None:
        return ""

    return " ".join(str(value).strip().lower().split())


def parse_date(value: Any) -> date | None:
    """
    Tente de parser une date selon les formats autorisés.
    """
    if not value:
        return None

    cleaned_value = str(value).strip()

    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(cleaned_value, date_format).date()
        except ValueError:
            continue

    return None


def safe_float(value: Any) -> float | None:
    """
    Convertit une valeur textuelle ou numérique en float de manière robuste.
    """
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
    """
    Vérifie si un IBAN respecte un format syntaxique de base.
    """
    if not iban:
        return False

    cleaned_iban = str(iban).replace(" ", "").upper()
    return bool(IBAN_REGEX.match(cleaned_iban))


def get_extracted_data(document: dict[str, Any]) -> dict[str, Any]:
    """
    Retourne le dictionnaire des données extraites d'un document.
    """
    return document.get("extractedData", {}) or {}


def get_field(
    document: dict[str, Any],
    field_name: str,
    default: Any = None,
) -> Any:
    """
    Récupère un champ métier dans extractedData.
    """
    extracted_data = get_extracted_data(document)
    return extracted_data.get(field_name, default)


def get_document_type(document: dict[str, Any]) -> str | None:
    """
    Retourne le type de document.
    """
    return document.get("documentType")


def get_vendor_id_from_documents(documents: list[dict[str, Any]]) -> str | None:
    """
    Retourne le vendorId à partir du premier document de la liste.
    """
    if not documents:
        return None

    return documents[0].get("vendorId")


def get_document_id(document: dict[str, Any]) -> Any:
    """
    Retourne l'identifiant technique du document.
    """
    return document.get("_id")


def get_document(
    documents: list[dict[str, Any]],
    document_type: str,
) -> dict[str, Any] | None:
    """
    Retourne le premier document correspondant au type demandé.
    """
    return next(
        (
            document
            for document in documents
            if get_document_type(document) == document_type
        ),
        None,
    )


def get_documents(
    documents: list[dict[str, Any]],
    document_types: list[str],
) -> list[dict[str, Any]]:
    """
    Retourne tous les documents correspondant à une liste de types.
    """
    return [
        document
        for document in documents
        if get_document_type(document) in document_types
    ]