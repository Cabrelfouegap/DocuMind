import os
import sys
import tempfile
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from pymongo import MongoClient
from bson import ObjectId
import gridfs
from callbacks import on_failure_callback

sys.path.insert(0, '/opt/airflow/ocr')

MONGO_URI = os.environ.get("MONGO_URI")

def traiter_documents_ocr(**context):
    client = MongoClient(MONGO_URI)
    db = client["hackathon_ipssi"]

    documents = list(db["rawdocuments"].find({"processingStatus": "PROCESSING"}))

    if not documents:
        print("[TRAITEMENT] Aucun document PROCESSING trouvé")
        client.close()
        return []

    from pipeline_ocr import traiter_doc

    fs = gridfs.GridFS(db, collection="datalake_raw")
    clean_ids = []

    for doc in documents:
        raw_id    = doc["_id"]
        file_name = doc["originalFileName"]
        stored_path = doc["storedFilePath"]

        # vendorId doit être stocké dans rawdocuments par Nassim/Hyndi
        # Fallback sur l'_id si absent — à corriger côté backend
        vendor_id = doc.get("vendorId", str(raw_id))

        try:
            grid_file = fs.find_one({"filename": stored_path})

            if not grid_file:
                print(f"[TRAITEMENT] Fichier GridFS introuvable : {file_name}")
                db["rawdocuments"].update_one(
                    {"_id": raw_id},
                    {"$set": {"processingStatus": "FAILED"}}
                )
                continue

            # Créer /tmp/<random>/<vendor_id>/filename
            # Cleg lit vendor_id via os.path.basename(os.path.dirname(chemin))
            tmp_dir    = tempfile.mkdtemp()
            vendor_dir = os.path.join(tmp_dir, vendor_id)
            os.makedirs(vendor_dir, exist_ok=True)
            tmp_path   = os.path.join(vendor_dir, file_name)

            with open(tmp_path, "wb") as f:
                f.write(grid_file.read())

            # Appel direct au module OCR de Cleg
            # Retourne {"vendor_id": "...", "documents": [{...}]}
            payload_ocr = traiter_doc(tmp_path)

            # Nettoyage fichier temporaire
            os.remove(tmp_path)
            os.rmdir(vendor_dir)
            os.rmdir(tmp_dir)

            # Extraire le texte depuis le premier document du payload
            documents_list = payload_ocr.get("documents", [])
            first_doc      = documents_list[0] if documents_list else {}
            confidence     = first_doc.get("ocr_confidence", 0)

            if isinstance(confidence, float) and confidence <= 1:
                confidence = round(confidence * 100, 2)

            clean_doc = {
                "rawDocumentId": raw_id,
                "extractedText": str(first_doc),   # texte brut non disponible dans payload métier
                "ocrEngineUsed": "EASYOCR",
                "confidenceScore": confidence,
                "ocrPayload": payload_ocr,          # payload complet pour dag_validation
            }

            result = db["cleandocuments"].insert_one(clean_doc)
            clean_ids.append(str(result.inserted_id))

            db["rawdocuments"].update_one(
                {"_id": raw_id},
                {"$set": {"processingStatus": "OCR_COMPLETED"}}
            )

            print(f"[TRAITEMENT] OK — {file_name} (vendor:{vendor_id}) → cleandocuments:{result.inserted_id}")

        except Exception as e:
            print(f"[TRAITEMENT] ERREUR — {file_name} : {e}")
            db["rawdocuments"].update_one(
                {"_id": raw_id},
                {"$set": {"processingStatus": "FAILED"}}
            )

    client.close()
    context["ti"].xcom_push(key="clean_document_ids", value=clean_ids)
    return clean_ids

with DAG(
    dag_id="dag_traitement",
    start_date=datetime(2026, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["traitement", "ocr"],
    default_args={
        "on_failure_callback": on_failure_callback,
        "retries": 2,
        "retry_delay": 30,
    }
) as dag:

    t1 = PythonOperator(
        task_id="traiter_documents_ocr",
        python_callable=traiter_documents_ocr,
        provide_context=True,
    )

    t2 = TriggerDagRunOperator(
        task_id="trigger_validation",
        trigger_dag_id="dag_validation",
        wait_for_completion=False,
    )

    t1 >> t2