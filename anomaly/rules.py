

RULES_CONFIG = {
    "LOW_OCR_CONFIDENCE": {
        "severity": "low",
        "score": 10,
        "message": "OCR confidence is too low, manual verification is recommended."
    },
    "MISSING_REQUIRED_FIELD": {
        "severity": "medium",
        "score": 10,
        "message": "One or more required fields are missing."
    },
    "URSSAF_EXPIRED": {
        "severity": "high",
        "score": 30,
        "message": "URSSAF certificate is expired."
    },
    "SIRET_MISMATCH": {
        "severity": "high",
        "score": 40,
        "message": "SIRET mismatch detected across vendor documents."
    },
    "COMPANY_NAME_MISMATCH": {
        "severity": "medium",
        "score": 25,
        "message": "Company name mismatch detected across vendor documents."
    },
    "QUOTE_INVOICE_PRICE_MISMATCH": {
        "severity": "medium",
        "score": 20,
        "message": "Quote and invoice total amounts do not match."
    },
    "VAT_INCONSISTENT": {
        "severity": "medium",
        "score": 20,
        "message": "VAT calculation is inconsistent with the total amount."
    },
    "RIB_ACCOUNT_HOLDER_MISMATCH": {
        "severity": "high",
        "score": 30,
        "message": "RIB account holder does not match company name."
    },
    "INVALID_IBAN_FORMAT": {
        "severity": "medium",
        "score": 15,
        "message": "Invalid IBAN format detected."
    }
}

REQUIRED_FIELDS = {
    "quote": [
        "company_name",
        "siret",
        "quote_number",
        "amount_ht",
        "vat_rate",
        "total_ttc",
        "quote_issue_date",
        "quote_validity_date"
    ],
    "invoice": [
        "company_name",
        "siret",
        "invoice_number",
        "amount_ht",
        "vat_rate",
        "total_ttc",
        "invoice_issue_date"
    ],
    "urssaf": [
        "company_name",
        "siret",
        "certificate_number",
        "issue_date",
        "expiration_date"
    ],
    "kbis": [
        "company_name",
        "siret",
        "legal_form",
        "creation_date",
        "address"
    ],
    "rib": [
        "bank_name",
        "iban",
        "bic",
        "account_holder"
    ]
}

OCR_CONFIDENCE_THRESHOLD = 0.80

VALID_STATUS_THRESHOLDS = {
    "VALID": (0, 19),
    "WARNING": (20, 49),
    "SUSPICIOUS": (50, 9999)
}