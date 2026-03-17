from __future__ import annotations

from datetime import date
from typing import Any

from rules import (
    AMOUNT_TOLERANCE,
    COMPANY_NAME_RELEVANT_DOCS,
    EXPECTED_DOCUMENT_TYPES,
    FINANCIAL_DOCS,
    HIGH_RISK_RULE_CODES,
    OCR_CONFIDENCE_THRESHOLD,
    REQUIRED_FIELDS,
    RULES_CONFIG,
    SIRET_RELEVANT_DOCS,
)
from utils import (
    get_document,
    get_document_id,
    get_document_type,
    get_documents,
    get_field,
    is_valid_iban,
    normalize_text,
    parse_date,
    safe_float,
)


def _stringify_document_id(doc: dict) -> str | None:
    document_id = get_document_id(doc)
    return str(document_id) if document_id is not None else None


def _build_document_context(doc: dict) -> dict:
    return {
        "documentId": _stringify_document_id(doc),
        "documentType": get_document_type(doc),
    }


def build_anomaly(
    code: str,
    details: dict | None = None,
    scope: str = "document",
) -> dict:
    rule = RULES_CONFIG[code]
    return {
        "anomalyCode": code,
        "severity": rule["severity"],
        "score": rule["score"],
        "message": rule["message"],
        "scope": scope,
        "details": details or {},
    }


def is_missing_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, list) and len(value) == 0:
        return True
    return False


def check_missing_required_documents(documents: list[dict]) -> list[dict]:
    present_types = {
        get_document_type(doc)
        for doc in documents
        if get_document_type(doc)
    }

    missing_types = [
        doc_type
        for doc_type in EXPECTED_DOCUMENT_TYPES
        if doc_type not in present_types
    ]

    if not missing_types:
        return []

    return [
        build_anomaly(
            "MISSING_REQUIRED_DOCUMENT",
            {"missingDocumentTypes": missing_types},
            scope="vendor",
        )
    ]


def check_low_ocr_confidence(documents: list[dict]) -> list[dict]:
    anomalies = []

    for doc in documents:
        confidence = safe_float(doc.get("ocrConfidence"))
        if confidence is None:
            continue

        if confidence < OCR_CONFIDENCE_THRESHOLD:
            anomalies.append(
                build_anomaly(
                    "LOW_OCR_CONFIDENCE",
                    {
                        **_build_document_context(doc),
                        "ocrConfidence": round(confidence, 4),
                    },
                    scope="document",
                )
            )

    return anomalies


def check_missing_required_fields(documents: list[dict]) -> list[dict]:
    anomalies = []

    for doc in documents:
        doc_type = get_document_type(doc)
        required_fields = REQUIRED_FIELDS.get(doc_type, [])

        missing_fields = [
            field
            for field in required_fields
            if is_missing_value(get_field(doc, field))
        ]

        if missing_fields:
            anomalies.append(
                build_anomaly(
                    "MISSING_REQUIRED_FIELD",
                    {
                        **_build_document_context(doc),
                        "missingFields": missing_fields,
                    },
                    scope="document",
                )
            )

    return anomalies


def check_siret_mismatch(documents: list[dict]) -> list[dict]:
    sirets = {}

    for doc in documents:
        doc_type = get_document_type(doc)
        siret = get_field(doc, "siret")

        if doc_type in SIRET_RELEVANT_DOCS and not is_missing_value(siret):
            sirets[doc_type] = str(siret).strip()

    if len(sirets) >= 2 and len(set(sirets.values())) > 1:
        return [build_anomaly("SIRET_MISMATCH", sirets, scope="vendor")]

    return []


def check_company_name_mismatch(documents: list[dict]) -> list[dict]:
    company_names = {}

    for doc in documents:
        doc_type = get_document_type(doc)
        company_name = get_field(doc, "company_name")

        if doc_type in COMPANY_NAME_RELEVANT_DOCS and not is_missing_value(company_name):
            company_names[doc_type] = normalize_text(company_name)

    if len(company_names) >= 2 and len(set(company_names.values())) > 1:
        return [build_anomaly("COMPANY_NAME_MISMATCH", company_names, scope="vendor")]

    return []


def check_quote_invoice_price_mismatch(documents: list[dict]) -> list[dict]:
    quote = get_document(documents, "quote")
    invoice = get_document(documents, "invoice")

    if not quote or not invoice:
        return []

    quote_total = safe_float(get_field(quote, "total_ttc"))
    invoice_total = safe_float(get_field(invoice, "total_ttc"))

    if quote_total is None or invoice_total is None:
        return []

    difference = abs(quote_total - invoice_total)

    if difference > AMOUNT_TOLERANCE:
        return [
            build_anomaly(
                "QUOTE_INVOICE_PRICE_MISMATCH",
                {
                    "quoteDocumentId": _stringify_document_id(quote),
                    "invoiceDocumentId": _stringify_document_id(invoice),
                    "quoteTotalTtc": round(quote_total, 2),
                    "invoiceTotalTtc": round(invoice_total, 2),
                    "difference": round(difference, 2),
                },
                scope="vendor",
            )
        ]

    return []


def check_vat_inconsistency(documents: list[dict]) -> list[dict]:
    anomalies = []

    for doc in get_documents(documents, FINANCIAL_DOCS):
        amount_ht = safe_float(get_field(doc, "amount_ht"))
        vat_rate = safe_float(get_field(doc, "vat_rate"))
        total_ttc = safe_float(get_field(doc, "total_ttc"))

        if amount_ht is None or vat_rate is None or total_ttc is None:
            continue

        expected_ttc = round(amount_ht * (1 + vat_rate / 100), 2)
        detected_ttc = round(total_ttc, 2)
        difference = abs(expected_ttc - detected_ttc)

        if difference > AMOUNT_TOLERANCE:
            anomalies.append(
                build_anomaly(
                    "VAT_INCONSISTENT",
                    {
                        **_build_document_context(doc),
                        "amountHt": round(amount_ht, 2),
                        "vatRate": round(vat_rate, 2),
                        "expectedTotalTtc": expected_ttc,
                        "detectedTotalTtc": detected_ttc,
                        "difference": round(difference, 2),
                    },
                    scope="document",
                )
            )

    return anomalies


def check_urssaf_expired(
    documents: list[dict],
    today: date | None = None,
) -> list[dict]:
    urssaf = get_document(documents, "urssaf")
    if not urssaf:
        return []

    current_date = today or date.today()
    expiration_date_raw = get_field(urssaf, "expiration_date")
    expiration_date = parse_date(expiration_date_raw)

    if expiration_date and expiration_date < current_date:
        return [
            build_anomaly(
                "URSSAF_EXPIRED",
                {
                    **_build_document_context(urssaf),
                    "expirationDate": expiration_date_raw,
                    "checkedAt": str(current_date),
                },
                scope="document",
            )
        ]

    return []


def check_rib_account_holder_mismatch(documents: list[dict]) -> list[dict]:
    rib = get_document(documents, "rib")
    if not rib:
        return []

    account_holder = normalize_text(get_field(rib, "account_holder"))
    company_name = normalize_text(get_field(rib, "company_name"))

    if account_holder and company_name and account_holder != company_name:
        return [
            build_anomaly(
                "RIB_ACCOUNT_HOLDER_MISMATCH",
                {
                    **_build_document_context(rib),
                    "accountHolder": get_field(rib, "account_holder"),
                    "companyName": get_field(rib, "company_name"),
                },
                scope="document",
            )
        ]

    return []


def check_invalid_iban_format(documents: list[dict]) -> list[dict]:
    rib = get_document(documents, "rib")
    if not rib:
        return []

    iban = get_field(rib, "iban")

    if iban and not is_valid_iban(iban):
        return [
            build_anomaly(
                "INVALID_IBAN_FORMAT",
                {
                    **_build_document_context(rib),
                    "iban": iban,
                },
                scope="document",
            )
        ]

    return []


def check_multiple_high_risk_signals(anomalies: list[dict]) -> list[dict]:
    detected_high_risk_rules = sorted(
        {
            anomaly["anomalyCode"]
            for anomaly in anomalies
            if anomaly["anomalyCode"] in HIGH_RISK_RULE_CODES
        }
    )

    if len(detected_high_risk_rules) >= 2:
        return [
            build_anomaly(
                "MULTIPLE_HIGH_RISK_SIGNALS",
                {"triggeredHighRiskRules": detected_high_risk_rules},
                scope="vendor",
            )
        ]

    return []


def compute_rule_score(anomalies: list[dict]) -> int:
    return sum(anomaly.get("score", 0) for anomaly in anomalies)


def detect_rule_based_anomalies(
    vendor_data: dict,
    today: date | None = None,
) -> list[dict]:
    documents = vendor_data.get("documents", [])

    anomalies = []
    anomalies.extend(check_missing_required_documents(documents))
    anomalies.extend(check_low_ocr_confidence(documents))
    anomalies.extend(check_missing_required_fields(documents))
    anomalies.extend(check_siret_mismatch(documents))
    anomalies.extend(check_company_name_mismatch(documents))
    anomalies.extend(check_quote_invoice_price_mismatch(documents))
    anomalies.extend(check_vat_inconsistency(documents))
    anomalies.extend(check_urssaf_expired(documents, today=today))
    anomalies.extend(check_rib_account_holder_mismatch(documents))
    anomalies.extend(check_invalid_iban_format(documents))
    anomalies.extend(check_multiple_high_risk_signals(anomalies))

    return anomalies