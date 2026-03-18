import os
from datetime import datetime

def on_failure_callback(context):
    dag_id = context.get("dag").dag_id
    task_id = context.get("task_instance").task_id
    execution_date = context.get("execution_date")
    exception = context.get("exception")

    print(f"[ERREUR] {datetime.utcnow().isoformat()} | DAG: {dag_id} | TASK: {task_id} | DATE: {execution_date} | EXCEPTION: {exception}")