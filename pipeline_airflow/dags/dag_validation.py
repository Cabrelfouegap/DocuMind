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

MONGO_URI = os.environ.get("MONGO_URI")
BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:5000")

def valider_et_stocker(**context):
    from engine import RuleBasedAnomalyDetector

    client = MongoClient(MONGO_URI)
    db = client["hackathon_ipssi"]

    clean_docs = list(db["cleandocuments"].find(
        {"ocrPayload": {"$exists": True}}
    ).sort("createdAt", 1))

    if not clean_docs:
        print("[VALIDATION] Aucun document à valider")
        client.close()
        return

    vendors = defaultdict(list)
    for doc in clean_docs:
        payload = doc.get("ocrPayload", {})
        vendor_id = payload.get("vendor_id", "unknown")

        documents_list = payload.get("documents", [])
        doc_data = documents_list[0] if documents_list else payload

        doc_data["_clean_doc_id"] = str(doc["_id"])
        doc_data["_raw_doc_id"] = str(doc["rawDocumentId"])
        vendors[vendor_id].append(doc_data)

    detector = RuleBasedAnomalyDetector()

    for vendor_id, documents in vendors.items():
        try:
            vendor_data = {
                "vendor_id": vendor_id,
                "documents": documents
            }

            result = detector.detect(vendor_data)
            validation = result.get("validation", {})

            for doc_data in documents:
                clean_doc_id = doc_data.get("_clean_doc_id")
                raw_doc_id = doc_data.get("_raw_doc_id")
                doc_type = doc_data.get("document_type", "unknown")

                extracted = {k: v for k, v in doc_data.items()
                             if not k.startswith("_") and k != "document_type"}

                curated_doc = {
                    "cleanDocumentId": ObjectId(clean_doc_id),
                    "vendorId": vendor_id,
                    "documentType": doc_type,
                    "extractedData": extracted,
                    "validation": {
                        "isValid": validation.get("isValid", False),
                        "ruleScoreRaw": validation.get("ruleScoreRaw", 0),
                        "ruleScoreNormalized": validation.get("ruleScoreNormalized", 0),
                        "finalScore": validation.get("finalScore", 0),
                        "status": validation.get("status", "UNKNOWN"),
                        "decision": validation.get("decision", "verification_manuelle"),
                        "anomalyCount": validation.get("anomalyCount", 0),
                        "lastCheckedAt": datetime.utcnow(),
                        "engineVersion": validation.get("engineVersion", ""),
                        "anomaliesDetected": validation.get("anomaliesDetected", []),
                    }
                }

                db["curateddocuments"].insert_one(curated_doc)
                print(f"[VALIDATION] {vendor_id}/{doc_type} → curated | valid={validation.get('isValid')}")

                remplir_frontends(raw_doc_id, curated_doc)

        except Exception as e:
            print(f"[VALIDATION] ERREUR vendor {vendor_id} : {e}")

    client.close()

def remplir_frontends(raw_doc_id, curated_doc):
    try:
        payload = {
            "status": "Conforme" if curated_doc["validation"]["isValid"] else "Non conforme",
            "aiGenerated": True,
            "reason": "",
            "type": curated_doc.get("documentType", ""),
            "extractedData": {
                "siret": curated_doc["extractedData"].get("siret", ""),
                "amountHT": curated_doc["extractedData"].get("amount_ht", 0),
                "amountTTC": curated_doc["extractedData"].get("total_ttc", 0),
                "emissionDate": curated_doc["extractedData"].get("invoice_issue_date", ""),
                "expirationDate": curated_doc["extractedData"].get("expiration_date", ""),
            }
        }

        if not curated_doc["validation"]["isValid"]:
            anomalies = curated_doc["validation"].get("anomaliesDetected", [])
            if anomalies:
                payload["reason"] = anomalies[0].get("message", "Anomalie détectée")

        response = requests.patch(
            f"{BACKEND_URL}/api/documents/{raw_doc_id}",
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        print(f"[VALIDATION] Frontend mis à jour pour {raw_doc_id}")

    except Exception as e:
        print(f"[VALIDATION] Erreur mise à jour frontend {raw_doc_id} : {e}")

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