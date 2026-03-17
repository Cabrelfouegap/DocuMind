from __future__ import annotations

from typing import Final


RULES_CONFIG: Final[dict[str, dict[str, object]]] = {
    "LOW_OCR_CONFIDENCE": {
        "severity": "low",
        "score": 10,
        "message": "La confiance OCR est faible, une vérification manuelle est recommandée.",
    },
    "MISSING_REQUIRED_FIELD": {
        "severity": "medium",
        "score": 10,
        "message": "Un ou plusieurs champs obligatoires sont manquants.",
    },
    "MISSING_REQUIRED_DOCUMENT": {
        "severity": "medium",
        "score": 15,
        "message": "Un ou plusieurs types de documents obligatoires sont manquants.",
    },
    "URSSAF_EXPIRED": {
        "severity": "high",
        "score": 30,
        "message": "L’attestation URSSAF est expirée.",
    },
    "SIRET_MISMATCH": {
        "severity": "high",
        "score": 40,
        "message": "Incohérence du SIRET détectée entre les documents.",
    },
    "COMPANY_NAME_MISMATCH": {
        "severity": "medium",
        "score": 25,
        "message": "Incohérence du nom de l’entreprise entre les documents.",
    },
    "QUOTE_INVOICE_PRICE_MISMATCH": {
        "severity": "medium",
        "score": 20,
        "message": "Les montants TTC du devis et de la facture ne correspondent pas.",
    },
    "VAT_INCONSISTENT": {
        "severity": "medium",
        "score": 20,
        "message": "Le calcul de la TVA est incohérent avec le montant total.",
    },
    "RIB_ACCOUNT_HOLDER_MISMATCH": {
        "severity": "high",
        "score": 30,
        "message": "Le titulaire du compte bancaire ne correspond pas au nom de l’entreprise.",
    },
    "INVALID_IBAN_FORMAT": {
        "severity": "medium",
        "score": 15,
        "message": "Le format de l’IBAN est invalide.",
    },
    "MULTIPLE_HIGH_RISK_SIGNALS": {
        "severity": "high",
        "score": 20,
        "message": "Plusieurs anomalies critiques ont été détectées pour ce fournisseur.",
    },
}


REQUIRED_FIELDS: Final[dict[str, list[str]]] = {
    "quote": [
        "company_name",
        "siret",
        "quote_number",
        "product_description",
        "amount_ht",
        "vat_rate",
        "total_ttc",
        "quote_issue_date",
        "quote_validity_date",
    ],
    "invoice": [
        "company_name",
        "siret",
        "invoice_number",
        "product_description",
        "amount_ht",
        "vat_rate",
        "total_ttc",
        "invoice_issue_date",
    ],
    "urssaf": [
        "company_name",
        "siret",
        "certificate_number",
        "issue_date",
        "expiration_date",
    ],
    "kbis": [
        "company_name",
        "siret",
        "legal_form",
        "creation_date",
        "address",
    ],
    "rib": [
        "bank_name",
        "iban",
        "bic",
        "account_holder",
        "company_name",
    ],
}


EXPECTED_DOCUMENT_TYPES: Final[list[str]] = [
    "quote",
    "invoice",
    "urssaf",
    "kbis",
    "rib",
]

SIRET_RELEVANT_DOCS: Final[list[str]] = [
    "quote",
    "invoice",
    "urssaf",
    "kbis",
]

COMPANY_NAME_RELEVANT_DOCS: Final[list[str]] = [
    "quote",
    "invoice",
    "urssaf",
    "kbis",
    "rib",
]

FINANCIAL_DOCS: Final[list[str]] = [
    "quote",
    "invoice",
]


HIGH_RISK_RULE_CODES: Final[set[str]] = {
    "URSSAF_EXPIRED",
    "SIRET_MISMATCH",
    "RIB_ACCOUNT_HOLDER_MISMATCH",
}


OCR_CONFIDENCE_THRESHOLD: Final[float] = 0.80
AMOUNT_TOLERANCE: Final[float] = 1.00

DATE_FORMATS: Final[list[str]] = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
]

STATUS_THRESHOLDS: Final[dict[str, tuple[int, int]]] = {
    "VALID": (0, 19),
    "WARNING": (20, 49),
    "SUSPICIOUS": (50, 9999),
}