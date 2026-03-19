import os
import sys
import requests
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from pymongo import MongoClient
from bson import ObjectId
from collections import defaultdict
from callbacks import on_failure_callback

sys.path.insert(0, '/opt/airflow/anomaly')

MONGO_URI   = os.environ.get("MONGO_URI")
BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:5000")


def valider_et_stocker(**context):
    from engine import RuleBasedAnomalyDetector
    from adapter import ensure_detector_input_format

    client = MongoClient(MONGO_URI)
    db     = client["hackathon_ipssi"]

    # Ne traiter QUE les documents pas encore dans curateddocuments
    already_curated = set(
        str(c["cleanDocumentId"])
        for c in db["curateddocuments"].find({}, {"cleanDocumentId": 1})
    )

    clean_docs = list(
        db["cleandocuments"].find({"ocrPayload": {"$exists": True}})
        .sort("createdAt", 1)
    )

    # Filtre : garder uniquement les non encore traités
    clean_docs = [d for d in clean_docs if str(d["_id"]) not in already_curated]

    if not clean_docs:
        print("[VALIDATION] Aucun nouveau document à valider")
        client.close()
        return

    print(f"[VALIDATION] {len(clean_docs)} document(s) à valider")

    # Regrouper par vendor_id
    vendors = defaultdict(list)
    for doc in clean_docs:
        payload   = doc.get("ocrPayload", {})
        vendor_id = payload.get("vendor_id") or payload.get("vendorId", "unknown")

        documents_list = payload.get("documents", [])
        doc_data = documents_list[0] if documents_list else {}

        # Clé de regroupement fournisseur :
        # 1. SIRET si présent
        # 2. Sinon company_name
        # 3. Sinon vendor_id fourni
        # 4. Sinon cleanDocumentId (clé unique de secours)
        siret = str(doc_data.get("siret", "") or "").strip()
        company = str(doc_data.get("company_name", "") or "").strip()
        raw_vendor = str(payload.get("vendor_id", "") or "").strip()

        if siret:
            vendor_key = siret
        elif company:
            vendor_key = company
        elif raw_vendor:
            vendor_key = raw_vendor
        else:
            vendor_key = str(doc.get("_id"))

        doc_data["_clean_doc_id"] = str(doc["_id"])
        doc_data["_raw_doc_id"]   = str(doc["rawDocumentId"])
        vendors[vendor_id].append(doc_data)

    detector = RuleBasedAnomalyDetector()

    for vendor_id, docs in vendors.items():
        try:
            raw_vendor_data = {
                "vendor_id": vendor_id,
                "documents": [
                    {k: v for k, v in d.items() if not k.startswith("_")}
                    for d in docs
                ]
            }

            normalized = ensure_detector_input_format(raw_vendor_data)
            result     = detector.detect(normalized)
            validation = result.get("validation", {})

            for doc_data in docs:
                clean_doc_id = doc_data.get("_clean_doc_id")
                raw_doc_id   = doc_data.get("_raw_doc_id")
                doc_type     = doc_data.get("document_type") or doc_data.get("documentType", "unknown")

                extracted = {
                    k: v for k, v in doc_data.items()
                    if not k.startswith("_")
                    and k not in ("document_type", "documentType", "ocr_confidence", "ocrConfidence")
                }

                curated_doc = {
                    "cleanDocumentId": ObjectId(clean_doc_id),
                    "vendorId":        vendor_id,
                    "documentType":    doc_type,
                    "extractedData":   extracted,
                    "validation": {
                        "isValid":             validation.get("isValid", False),
                        "ruleScoreRaw":        validation.get("ruleScoreRaw", 0),
                        "ruleScoreNormalized": validation.get("ruleScoreNormalized", 0),
                        "finalScore":          validation.get("finalScore", 0),
                        "status":              validation.get("status", "UNKNOWN"),
                        "decision":            validation.get("decision", "verification_manuelle"),
                        "anomalyCount":        validation.get("anomalyCount", 0),
                        "lastCheckedAt":       datetime.utcnow(),
                        "engineVersion":       validation.get("engineVersion", ""),
                        "anomaliesDetected":   validation.get("anomaliesDetected", []),
                    }
                }

                db["curateddocuments"].insert_one(curated_doc)
                print(f"[VALIDATION] {vendor_id}/{doc_type} → curated | isValid={validation.get('isValid')} | score={validation.get('finalScore')}")

                remplir_frontends(raw_doc_id, curated_doc, canon_siret, canon_company)

        except Exception as e:
            print(f"[VALIDATION] ERREUR vendor {vendor_id} : {e}")

    client.close()


def remplir_frontends(raw_doc_id, curated_doc):
    try:
        validation = curated_doc.get("validation", {}) or {}
        is_valid = validation.get("isValid", False)
        engine_status = (validation.get("status") or "").upper()
        anomalies = validation.get("anomaliesDetected", []) or []

        extracted = curated_doc.get("extractedData", {}) or {}

        # Mapping moteur -> statuts frontend
        # VALID -> Conforme | WARNING -> Warning | SUSPICIOUS/other -> Non conforme
        if engine_status == "VALID":
            front_status = "Conforme"
        elif engine_status == "WARNING":
            front_status = "Warning"
        else:
            front_status = "Non conforme"

        payload = {
            "status":      front_status,
            "aiGenerated": True,
            "reason":      anomalies[0].get("message", "") if anomalies and front_status != "Conforme" else "",
            "type":        curated_doc.get("documentType", ""),
            "extractedData": {
                "siret":          extracted.get("siret", ""),
                "companyName":    extracted.get("company_name") or extracted.get("companyName", ""),
                "amountHT":       extracted.get("amount_ht", 0),
                "amountTTC":      extracted.get("total_ttc", 0),
                "emissionDate":   extracted.get("invoice_issue_date", ""),
                "expirationDate": extracted.get("expiration_date", ""),
            }
        }

        response = requests.patch(
            f"{BACKEND_URL}/api/documents/{raw_doc_id}",
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        print(f"[VALIDATION] Frontend mis à jour → {raw_doc_id}")

    except Exception as e:
        print(f"[VALIDATION] Erreur frontend {raw_doc_id} : {e}")


with DAG(
    dag_id="dag_validation",
    start_date=datetime(2026, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["validation", "anomalie"],
    default_args={
        "on_failure_callback": on_failure_callback,
        "retries": 2,
        "retry_delay": 30,
    }
) as dag:

    t1 = PythonOperator(
        task_id="valider_et_stocker",
        python_callable=valider_et_stocker,
        provide_context=True,
    )

