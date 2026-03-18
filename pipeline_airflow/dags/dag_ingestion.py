import os
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from pymongo import MongoClient
from bson import ObjectId
from callbacks import on_failure_callback

MONGO_URI = os.environ.get("MONGO_URI")

def scanner_documents_pending(**context):
    client = MongoClient(MONGO_URI)
    db = client["hackathon_ipssi"]

    documents = list(db["rawdocuments"].find({"processingStatus": "PENDING"}))
    client.close()

    if not documents:
        print("[INGESTION] Aucun document PENDING trouvé")
        return []

    ids = [str(doc["_id"]) for doc in documents]
    print(f"[INGESTION] {len(ids)} document(s) PENDING : {ids}")
    context["ti"].xcom_push(key="raw_document_ids", value=ids)
    return ids

def marquer_en_processing(**context):
    ids = context["ti"].xcom_pull(task_ids="scanner_documents_pending", key="raw_document_ids")
    if not ids:
        return

    client = MongoClient(MONGO_URI)
    db = client["hackathon_ipssi"]
    db["rawdocuments"].update_many(
        {"_id": {"$in": [ObjectId(i) for i in ids]}},
        {"$set": {"processingStatus": "PROCESSING"}}
    )
    client.close()
    print(f"[INGESTION] {len(ids)} document(s) → PROCESSING")

with DAG(
    dag_id="dag_ingestion",
    start_date=datetime(2026, 1, 1),
    schedule_interval="*/2 * * * *",
    catchup=False,
    tags=["ingestion"],
    default_args={
        "on_failure_callback": on_failure_callback,
        "retries": 2,
        "retry_delay": 30,
    }
) as dag:

    t1 = PythonOperator(
        task_id="scanner_documents_pending",
        python_callable=scanner_documents_pending,
        provide_context=True,
    )

    t2 = PythonOperator(
        task_id="marquer_en_processing",
        python_callable=marquer_en_processing,
        provide_context=True,
    )

    t3 = TriggerDagRunOperator(
        task_id="trigger_traitement",
        trigger_dag_id="dag_traitement",
        wait_for_completion=False,
    )

    t1 >> t2 >> t3