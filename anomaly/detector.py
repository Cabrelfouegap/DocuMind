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


def stringify_document_id(document: dict[str, Any]) -> str | None:
    """
    Convertit l'identifiant d'un document en chaîne de caractères.
    """
    document_id = get_document_id(document)
    return str(document_id) if document_id is not None else None


def build_document_context(document: dict[str, Any]) -> dict[str, Any]:
    """
    Construit un contexte minimal réutilisable dans les anomalies.
    """
    return {
        "documentId": stringify_document_id(document),
        "documentType": get_document_type(document),
    }


def build_anomaly(
    code: str,
    details: dict[str, Any] | None = None,
    scope: str = "document",
) -> dict[str, Any]:
    """
    Construit une anomalie standardisée à partir de la configuration métier.
    """
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
    """
    Détermine si une valeur doit être considérée comme absente.
    """
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, list) and not value:
        return True
    return False


def check_missing_required_documents(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Vérifie si certains types de documents obligatoires sont absents.
    """
    present_document_types = {
        get_document_type(document)
        for document in documents
        if get_document_type(document)
    }

    missing_document_types = [
        document_type
        for document_type in EXPECTED_DOCUMENT_TYPES
        if document_type not in present_document_types
    ]

    if not missing_document_types:
        return []

    return [
        build_anomaly(
            "MISSING_REQUIRED_DOCUMENT",
            {"missingDocumentTypes": missing_document_types},
            scope="vendor",
        )
    ]


def check_low_ocr_confidence(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Détecte les documents dont le score de confiance OCR est inférieur au seuil défini.
    """
    anomalies: list[dict[str, Any]] = []

    for document in documents:
        confidence = safe_float(document.get("ocrConfidence"))
        if confidence is None:
            continue

        if confidence < OCR_CONFIDENCE_THRESHOLD:
            anomalies.append(
                build_anomaly(
                    "LOW_OCR_CONFIDENCE",
                    {
                        **build_document_context(document),
                        "ocrConfidence": round(confidence, 4),
                    },
                    scope="document",
                )
            )

    return anomalies


def check_missing_required_fields(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Vérifie la présence des champs obligatoires selon le type de document.
    """
    anomalies: list[dict[str, Any]] = []

    for document in documents:
        document_type = get_document_type(document)
        required_fields = REQUIRED_FIELDS.get(document_type, [])

        missing_fields = [
            field_name
            for field_name in required_fields
            if is_missing_value(get_field(document, field_name))
        ]

        if missing_fields:
            anomalies.append(
                build_anomaly(
                    "MISSING_REQUIRED_FIELD",
                    {
                        **build_document_context(document),
                        "missingFields": missing_fields,
                    },
                    scope="document",
                )
            )

    return anomalies


def check_siret_mismatch(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Vérifie la cohérence du SIRET entre les documents pertinents.
    """
    sirets_by_document_type: dict[str, str] = {}

    for document in documents:
        document_type = get_document_type(document)
        siret = get_field(document, "siret")

        if document_type in SIRET_RELEVANT_DOCS and not is_missing_value(siret):
            sirets_by_document_type[document_type] = str(siret).strip()

    if len(sirets_by_document_type) >= 2 and len(set(sirets_by_document_type.values())) > 1:
        return [
            build_anomaly(
                "SIRET_MISMATCH",
                sirets_by_document_type,
                scope="vendor",
            )
        ]

    return []


def check_company_name_mismatch(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Vérifie la cohérence du nom d'entreprise entre les documents pertinents.
    """
    company_names_by_document_type: dict[str, str] = {}

    for document in documents:
        document_type = get_document_type(document)
        company_name = get_field(document, "company_name")

        if document_type in COMPANY_NAME_RELEVANT_DOCS and not is_missing_value(company_name):
            company_names_by_document_type[document_type] = normalize_text(company_name)

    if len(company_names_by_document_type) >= 2 and len(set(company_names_by_document_type.values())) > 1:
        return [
            build_anomaly(
                "COMPANY_NAME_MISMATCH",
                company_names_by_document_type,
                scope="vendor",
            )
        ]

    return []


def check_quote_invoice_price_mismatch(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Compare les montants TTC du devis et de la facture.
    """
    quote_document = get_document(documents, "quote")
    invoice_document = get_document(documents, "invoice")

    if not quote_document or not invoice_document:
        return []

    quote_total_ttc = safe_float(get_field(quote_document, "total_ttc"))
    invoice_total_ttc = safe_float(get_field(invoice_document, "total_ttc"))

    if quote_total_ttc is None or invoice_total_ttc is None:
        return []

    difference = abs(quote_total_ttc - invoice_total_ttc)

    if difference > AMOUNT_TOLERANCE:
        return [
            build_anomaly(
                "QUOTE_INVOICE_PRICE_MISMATCH",
                {
                    "quoteDocumentId": stringify_document_id(quote_document),
                    "invoiceDocumentId": stringify_document_id(invoice_document),
                    "quoteTotalTtc": round(quote_total_ttc, 2),
                    "invoiceTotalTtc": round(invoice_total_ttc, 2),
                    "difference": round(difference, 2),
                },
                scope="vendor",
            )
        ]

    return []


def check_vat_inconsistency(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Vérifie la cohérence du calcul TVA sur les documents financiers.
    """
    anomalies: list[dict[str, Any]] = []

    for document in get_documents(documents, FINANCIAL_DOCS):
        amount_ht = safe_float(get_field(document, "amount_ht"))
        vat_rate = safe_float(get_field(document, "vat_rate"))
        total_ttc = safe_float(get_field(document, "total_ttc"))

        if amount_ht is None or vat_rate is None or total_ttc is None:
            continue

        expected_total_ttc = round(amount_ht * (1 + vat_rate / 100), 2)
        detected_total_ttc = round(total_ttc, 2)
        difference = abs(expected_total_ttc - detected_total_ttc)

        if difference > AMOUNT_TOLERANCE:
            anomalies.append(
                build_anomaly(
                    "VAT_INCONSISTENT",
                    {
                        **build_document_context(document),
                        "amountHt": round(amount_ht, 2),
                        "vatRate": round(vat_rate, 2),
                        "expectedTotalTtc": expected_total_ttc,
                        "detectedTotalTtc": detected_total_ttc,
                        "difference": round(difference, 2),
                    },
                    scope="document",
                )
            )

    return anomalies


def check_urssaf_expired(
    documents: list[dict[str, Any]],
    today: date | None = None,
) -> list[dict[str, Any]]:
    """
    Vérifie si l'attestation URSSAF est expirée.
    """
    urssaf_document = get_document(documents, "urssaf")
    if not urssaf_document:
        return []

    current_date = today or date.today()
    expiration_date_raw = get_field(urssaf_document, "expiration_date")
    expiration_date = parse_date(expiration_date_raw)

    if expiration_date and expiration_date < current_date:
        return [
            build_anomaly(
                "URSSAF_EXPIRED",
                {
                    **build_document_context(urssaf_document),
                    "expirationDate": expiration_date_raw,
                    "checkedAt": str(current_date),
                },
                scope="document",
            )
        ]

    return []


def check_rib_account_holder_mismatch(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Vérifie si le titulaire du compte bancaire correspond au nom de l'entreprise.
    """
    rib_document = get_document(documents, "rib")
    if not rib_document:
        return []

    account_holder = normalize_text(get_field(rib_document, "account_holder"))
    company_name = normalize_text(get_field(rib_document, "company_name"))

    if account_holder and company_name and account_holder != company_name:
        return [
            build_anomaly(
                "RIB_ACCOUNT_HOLDER_MISMATCH",
                {
                    **build_document_context(rib_document),
                    "accountHolder": get_field(rib_document, "account_holder"),
                    "companyName": get_field(rib_document, "company_name"),
                },
                scope="document",
            )
        ]

    return []


def check_invalid_iban_format(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Vérifie la validité syntaxique de l'IBAN.
    """
    rib_document = get_document(documents, "rib")
    if not rib_document:
        return []

    iban = get_field(rib_document, "iban")

    if iban and not is_valid_iban(iban):
        return [
            build_anomaly(
                "INVALID_IBAN_FORMAT",
                {
                    **build_document_context(rib_document),
                    "iban": iban,
                },
                scope="document",
            )
        ]

    return []


def check_multiple_high_risk_signals(anomalies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Détecte si plusieurs anomalies à haut risque sont présentes simultanément.
    """
    triggered_high_risk_rules = sorted(
        {
            anomaly["anomalyCode"]
            for anomaly in anomalies
            if anomaly["anomalyCode"] in HIGH_RISK_RULE_CODES
        }
    )

    if len(triggered_high_risk_rules) >= 2:
        return [
            build_anomaly(
                "MULTIPLE_HIGH_RISK_SIGNALS",
                {"triggeredHighRiskRules": triggered_high_risk_rules},
                scope="vendor",
            )
        ]

    return []


def compute_rule_score(anomalies: list[dict[str, Any]]) -> int:
    """
    Calcule le score brut total à partir des anomalies détectées.
    """
    return sum(anomaly.get("score", 0) for anomaly in anomalies)


def detect_rule_based_anomalies(
    vendor_data: dict[str, Any],
    today: date | None = None,
) -> list[dict[str, Any]]:
    """
    Exécute l'ensemble des règles métier sur les documents d'un fournisseur.
    """
    documents = vendor_data.get("documents", [])

    anomalies: list[dict[str, Any]] = []

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