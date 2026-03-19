# DocuMind

DocuMind est une plateforme intelligente de traitement automatique de documents administratifs fournisseurs. Elle permet à une entreprise de gérer, analyser et valider des pièces comptables et administratives - factures, devis, attestations URSSAF, Kbis, RIB - sans aucune intervention manuelle, grâce à une chaîne de traitement automatisée pilotée par intelligence artificielle.

---

## Problématique

Les entreprises traitent quotidiennement des dizaines de documents administratifs hétérogènes, souvent scannés ou de mauvaise qualité. Un opérateur doit lire chaque document, extraire les informations clés, vérifier la cohérence entre les documents d'un même fournisseur, saisir les données dans les systèmes internes et valider la conformité réglementaire. Ce processus est chronophage, sujet aux erreurs et non scalable.

## Solution

DocuMind automatise entièrement ce processus. Un document uploadé est automatiquement lu par OCR, ses données sont extraites et structurées, la cohérence inter-documents est vérifiée par un moteur de règles métier, et les résultats sont poussés automatiquement dans les interfaces métier sans que l'utilisateur n'ait à intervenir.

---

## Équipe

| Rôle | Membre | Dossier |
|---|---|---|
| Chef de projet + Pipeline Engineer | Narcisse TSAFACK | `pipeline_airflow/` `Docker/` |
| Frontend + API | Hyndi FANNIR | `backend/` `frontend/` |
| Liaison API / BDD | Nassim BOUFALOUS | `backend/` `database/` |
| Chef BDD NoSQL | Mohammed MOSLEH | `database/` |
| Responsable OCR | Cleg LOUFOUA | `Cleg-partie_ocr/` |
| Anomaly Detector | Ikhlas LAGHMICH | `anomaly/` |
| Scénario Maker + Dataset | Omomene IWELOMEN | `dataset/` `generator.py` |

---

## Architecture globale

```
Utilisateur
    ↓  upload PDF / image
Frontend React (port 5173)
    ↓  POST /api/documents/upload
Backend Express (port 5000)
    ↓  stockage fichier dans GridFS (bucket datalake_raw)
    ↓  création rawdocument { processingStatus: PENDING }
MongoDB (port 27017)
    ↓  Airflow détecte PENDING toutes les 2 minutes
Apache Airflow (port 8080)
    ↓  dag_ingestion → dag_traitement → dag_validation
OCR Cleg (import direct dans Airflow)
    ↓  traiter_doc(fichier) → JSON structuré → cleandocuments
Moteur anomalies Ikhlas (import direct dans Airflow)
    ↓  RuleBasedAnomalyDetector().detect(vendor_data) → curateddocuments
    ↓  PATCH /api/documents/:id
Frontend mis à jour automatiquement
```

---

## Data Lake - Architecture Medallion

| Zone | Collection MongoDB | Contenu |
|---|---|---|
| Raw / Bronze | `rawdocuments` + `datalake_raw` (GridFS) | Fichiers bruts uploadés, statuts PENDING → PROCESSING → OCR_COMPLETED |
| Clean / Silver | `cleandocuments` | Texte OCR extrait, payload structuré par type de document |
| Gold / Curated | `curateddocuments` | Données métier validées, score d'anomalie, décision finale |

---

## Pipeline Airflow - 3 DAGs

### DAG Ingestion (`dag_ingestion.py`)
- **Schedule** : toutes les 2 minutes
- **Tâche 1** `scanner_documents_pending` - interroge `rawdocuments`, détecte les documents avec `processingStatus: PENDING`
- **Tâche 2** `marquer_en_processing` - passe les documents à `PROCESSING`
- **Tâche 3** `trigger_traitement` - déclenche `dag_traitement`

### DAG Traitement (`dag_traitement.py`)
- **Schedule** : déclenché par `dag_ingestion`
- Récupère le fichier depuis GridFS via `storedFilePath`
- Crée un chemin temporaire `/tmp/<uuid>/<vendor_id>/filename` pour que l'OCR récupère le bon identifiant fournisseur
- Appelle `traiter_doc(chemin)` du module OCR de Cleg
- Stocke le payload structuré dans `cleandocuments`
- Passe le document à `OCR_COMPLETED`
- Déclenche `dag_validation`

### DAG Validation (`dag_validation.py`)
- **Schedule** : déclenché par `dag_traitement`
- Filtre anti-doublon : ne retraite pas les documents déjà dans `curateddocuments`
- Regroupe les documents par `vendor_id` - le moteur d'anomalies a besoin de tous les documents d'un même fournisseur pour les vérifications inter-documents
- Appelle `ensure_detector_input_format()` puis `RuleBasedAnomalyDetector().detect()`
- Stocke les résultats dans `curateddocuments`
- Appelle `PATCH /api/documents/:id` sur le backend pour mettre à jour le frontend en temps réel

---

## Détection d'anomalies

Le moteur de règles d'Ikhlas (`anomaly/engine.py`) vérifie pour chaque groupe de documents fournisseur :

| Règle | Sévérité | Score |
|---|---|---|
| SIRET incohérent entre documents | HIGH | 40 pts |
| Attestation URSSAF expirée | HIGH | 30 pts |
| Titulaire RIB ≠ nom entreprise | HIGH | 30 pts |
| Montant devis ≠ facture | MEDIUM | 30 pts |
| TVA incohérente | MEDIUM | 30 pts |
| IBAN invalide | MEDIUM | 30 pts |
| Champs obligatoires manquants | MEDIUM | 10–15 pts |
| Confiance OCR faible (< 80%) | LOW | 10 pts |
| Plusieurs signaux critiques simultanés | HIGH | 30 pts |

### Seuils de décision

| Score normalisé | Statut | Décision |
|---|---|---|
| 0 – 19 | VALID | Validation automatique → **Conforme** |
| 20 – 49 | WARNING | Vérification recommandée → **Warning** |
| 50+ | SUSPICIOUS | Vérification obligatoire → **Non conforme** |

---

## Interfaces utilisateur

**CRM Fournisseurs** (`/`) - Vue métier regroupant les documents par fournisseur. Affiche le statut de conformité et les données extraites.

**Outil de Conformité** (`/conformity`) - Interface de validation permettant l'upload de documents, le déclenchement de l'analyse IA, la consultation des anomalies détectées et la gestion manuelle des statuts.

---

## Stack technique

| Composant | Technologie |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, Axios |
| Backend | Node.js, Express.js, Mongoose, Multer |
| Base de données | MongoDB 7.0, GridFS |
| OCR | EasyOCR, PyMuPDF, spaCy (fr_core_news_md) |
| Détection anomalies | Python, moteur de règles métier |
| Orchestration | Apache Airflow 2.9.1, LocalExecutor |
| Conteneurisation | Docker, Docker Compose |

---

## Structure du projet

```
DocuMind/
├── .env.example                    ← variables d'environnement à copier
├── docker-compose.yml              ← orchestration Docker (Narcisse)
├── generator.py                    ← génération dataset (Omomene)
│
├── Docker/                         ← Docker des différents App (Narcisse)
│   ├── airflow/Dockerfile          ← image Airflow + dépendances OCR
│   ├── backend/Dockerfile
│   └── frontend/Dockerfile
│
├── Cleg-partie_ocr/                ← module OCR (Cleg)
│   ├── pipeline_ocr.py             ← point d'entrée : traiter_doc(chemin)
│   ├── extraction_texte.py
│   ├── nettoyage.py
│   ├── entites.py
│   ├── structuration.py
│   └── evaluation.py
│
├── anomaly/                        ← moteur détection anomalies (Ikhlas)
│   ├── engine.py                   ← RuleBasedAnomalyDetector
│   ├── detector.py
│   ├── rules.py
│   ├── adapter.py                  ← ensure_detector_input_format()
│   └── batch_processor.py
│
├── backend/                        ← API Express (Hyndi + Nassim)
│   ├── server.js
│   ├── config/multer.js
│   ├── models/Document.js
│   ├── models/CuratedDocument.js
│   └── routes/
│       ├── documents.js            ← upload, GET, PATCH, analyze
│       └── conformity.js
│
├── database/                       ← modèles MongoDB + GridFS (Mohammed)
│   ├── models/RawDocument.js
│   ├── models/CleanDocument.js
│   ├── models/CuratedDocument.js
│   └── middlewares/datalakeUpload.js
│
├── frontend/                       ← interface React (Hyndi)
│   └── src/
│       ├── pages/CRMView.jsx
│       ├── pages/ConformityView.jsx
│       └── api/documents.js
│
└── pipeline_airflow/               ← DAGs Airflow (Narcisse)
    └── dags/
        ├── dag_ingestion.py
        ├── dag_traitement.py
        ├── dag_validation.py
        └── callbacks.py
```

---

## Lancement

### Prérequis

- Docker Desktop installé et démarré
- Git

### Démarrage en une commande

```bash
git clone <url-du-repo>
cd DocuMind
cp .env.example .env
docker compose up -d --build
```

Docker démarre automatiquement tous les services. Le service `airflow-init` initialise la base de données Airflow et crée l'utilisateur admin au premier démarrage.

### Vérification

```bash
docker compose ps
```

Tous les conteneurs doivent être en statut `running` ou `healthy`.

### Arrêt

```bash
docker compose down
```

Pour supprimer également les volumes (reset complet) :

```bash
docker compose down -v
```

---

## Accès aux services

| Service | URL | Identifiants |
|---|---|---|
| Frontend CRM | http://localhost:5173 | - |
| Frontend Conformité | http://localhost:5173/conformity | - |
| Backend API | http://localhost:5000/api/documents | - |
| Airflow | http://localhost:8080 | user / password |
| MongoDB | localhost:27017 | user / password |

---

## Variables d'environnement

Fichier `.env` à la racine du projet (copier depuis `.env.example`) :

```env
MONGO_ROOT_USER=
MONGO_ROOT_PASSWORD=
AIRFLOW_FERNET_KEY=
```

---

## Routes API

| Méthode | Route | Description |
|---|---|---|
| GET | `/api/documents` | Liste tous les documents |
| POST | `/api/documents/upload` | Upload un ou plusieurs fichiers (multipart/form-data) |
| PATCH | `/api/documents/:id` | Met à jour statut, données extraites - appelé par Airflow |
| POST | `/api/documents/:id/analyze` | Remet le document à PENDING pour relancer le pipeline |

---

## Génération du dataset

`generator.py` à la racine génère 20 fournisseurs avec 5 documents chacun et des scénarios d'anomalies réalistes (SIRET incohérent, URSSAF expirée, montants différents, RIB incorrect, documents floutés ou pivotés). Utilisé uniquement par Omomene pour alimenter `dataset/`.

```bash
pip install faker jinja2 pdfkit pdf2image opencv-python
python generator.py
```

---

## Monitoring du pipeline

En cas d'échec d'une tâche, le callback `on_failure_callback` dans `callbacks.py` log automatiquement le DAG, la tâche, la date et l'exception. Chaque DAG est configuré avec 2 retries et un délai de 30 secondes entre chaque tentative.

Les logs sont accessibles dans l'interface Airflow à http://localhost:8080 ou directement dans `pipeline_airflow/logs/`.
