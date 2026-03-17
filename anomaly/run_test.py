from engine import RuleBasedAnomalyDetector

vendor_json = {
    "vendor_id": "vendor_01",
    "documents": [
        {
            "document_type": "quote",
            "company_name": "ABC SARL",
            "siret": "12345678900012",
            "quote_number": "Q001",
            "product_description": "IT equipment",
            "amount_ht": 1000,
            "vat_rate": 20,
            "total_ttc": 1200,
            "quote_issue_date": "2026-03-01",
            "quote_validity_date": "2026-03-31",
            "ocr_confidence": 0.95
        },
        {
            "document_type": "invoice",
            "company_name": "ABC SARL",
            "siret": "12345678900099",
            "invoice_number": "F001",
            "product_description": "IT equipment",
            "amount_ht": 1000,
            "vat_rate": 20,
            "total_ttc": 1300,
            "invoice_issue_date": "2026-03-05",
            "ocr_confidence": 0.78
        },
        {
            "document_type": "urssaf",
            "company_name": "ABC SARL",
            "siret": "12345678900012",
            "certificate_number": "URS001",
            "issue_date": "2025-01-01",
            "expiration_date": "2025-06-01",
            "ocr_confidence": 0.88
        },
        {
            "document_type": "kbis",
            "company_name": "ABC SARL",
            "siret": "12345678900012",
            "legal_form": "SARL",
            "creation_date": "2018-01-01",
            "address": "Paris",
            "ocr_confidence": 0.93
        },
        {
            "document_type": "rib",
            "bank_name": "BNP Paribas",
            "iban": "FR7612345678901234567890123",
            "bic": "BNPAFRPP",
            "account_holder": "XYZ SARL",
            "company_name": "ABC SARL",
            "ocr_confidence": 0.91
        }
    ]
}

detector = RuleBasedAnomalyDetector()
result = detector.detect(vendor_json)

print("=== RESULT ===")
print(result)