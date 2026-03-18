# Pipeline Airflow

Responsable : Narcisse TSAFACK

## Structure

```
pipeline_airflow/
├── dags/
│   ├── dag_ingestion.py    — détecte les PENDING toutes les 2 min
│   ├── dag_traitement.py   — OCR via Cleg, stocke dans cleandocuments
│   ├── dag_validation.py   — anomalies via Ikhlas, stocke dans curateddocuments
│   └── callbacks.py        — gestion des erreurs et retries
├── logs/                   — généré par Airflow
└── plugins/                — extensions Airflow (vide)
```

## Flux du pipeline

```
rawdocuments (PENDING)
        ↓ dag_ingestion
rawdocuments (PROCESSING)
        ↓ dag_traitement — lit GridFS, appelle traiter_doc()
cleandocuments
        ↓ dag_validation — appelle RuleBasedAnomalyDetector()
curateddocuments
        ↓ PATCH /api/documents/:id
Frontend mis à jour
```

## Modules importés directement

| Module | Chemin dans le conteneur | Fonction appelée |
|---|---|---|
| OCR (Cleg) | `/opt/airflow/ocr` | `traiter_doc(chemin_fichier)` |
| Anomalie (Ikhlas) | `/opt/airflow/anomaly` | `RuleBasedAnomalyDetector().detect(vendor_data)` |

## Monitoring

Chaque DAG a `retries: 2` et `retry_delay: 30s`. En cas d'échec après 2 tentatives, `on_failure_callback` est appelé et log l'erreur avec le DAG, la tâche, la date et l'exception.

## Statuts rawdocuments

| Statut | Signification |
|---|---|
| `PENDING` | Uploadé, en attente de traitement |
| `PROCESSING` | Pris en charge par Airflow |
| `OCR_COMPLETED` | OCR terminé, stocké dans cleandocuments |
| `FAILED` | Erreur pendant le traitement |