# DocuMind

DocuMind est une plateforme intelligente de traitement automatique de documents administratifs fournisseurs. Elle permet à une entreprise de gérer, analyser et valider des pièces comptables et administratives (factures, devis, attestations URSSAF, Kbis, RIB) sans intervention manuelle, grâce à une chaîne de traitement automatisée pilotée par intelligence artificielle.

## Problématique

Les entreprises traitent quotidiennement des milliers de documents administratifs hétérogènes, non structurés, parfois scannés ou de mauvaise qualité. Un opérateur doit lire chaque document, extraire les informations clés, vérifier la cohérence entre les documents d'un même fournisseur, saisir les données dans plusieurs systèmes internes et valider la conformité réglementaire. Ce processus est chronophage, sujet aux erreurs et non scalable.

## Solution

DocuMind automatise entièrement ce processus. Un document uploadé est automatiquement lu par OCR, ses données clés sont extraites et structurées, la cohérence inter-documents est vérifiée par un moteur de règles métier, et les résultats sont poussés automatiquement dans les applications métiers (CRM fournisseurs et outil de conformité).

## Architecture globale

```
Utilisateur
    ↓ upload PDF / image
Frontend (React) — port 5173
    ↓ POST /api/documents/upload
Backend (Express) — port 5000
    ↓ stockage fichier dans GridFS
    ↓ création document dans rawdocuments { processingStatus: PENDING }
MongoDB — port 27017
    ↓ Airflow détecte PENDING toutes les 2 minutes
Airflow — port 8080
    ↓ DAG ingestion → DAG traitement → DAG validation
OCR (Cleg) — import direct dans Airflow
    ↓ traiter_doc(fichier) → JSON structuré → cleandocuments
Anomaly Detector (Ikhlas) — import direct dans Airflow
    ↓ RuleBasedAnomalyDetector().detect(vendor_data) → curateddocuments
    ↓ PATCH /api/documents/:id
Frontend mis à jour automatiquement
```

## Architecture Data Lake (Medallion)

| Zone | Collection MongoDB | Contenu |
|---|---|---|
| Raw / Bronze | `rawdocuments` + `datalake_raw` (GridFS) | Fichiers bruts uploadés |
| Clean / Silver | `cleandocuments` | Texte OCR extrait + payload structuré |
| Curated / Gold | `curateddocuments` | Données métier validées + résultats anomalies |

## Pipeline Airflow

| DAG | Déclenchement | Rôle |
|---|---|---|
| `dag_ingestion` | Toutes les 2 minutes | Détecte les PENDING, passe à PROCESSING |
| `dag_traitement` | Déclenché par dag_ingestion | OCR via Cleg, stocke dans cleandocuments |
| `dag_validation` | Déclenché par dag_traitement | Anomalies via Ikhlas, stocke dans curateddocuments, met à jour le frontend |

## Détection d'anomalies

Le moteur de règles d'Ikhlas vérifie pour chaque fournisseur :

| Règle | Sévérité |
|---|---|
| SIRET incohérent entre documents | Haute |
| Attestation URSSAF expirée | Haute |
| Titulaire RIB différent du nom entreprise | Haute |
| Montant devis / facture différent | Moyenne |
| TVA incohérente | Moyenne |
| Champs obligatoires manquants | Moyenne |
| Confiance OCR faible | Faible |

Le résultat est un score normalisé entre 0 et 100 :

| Score | Statut | Décision |
|---|---|---|
| 0 — 19 | VALID | Validation automatique |
| 20 — 49 | WARNING | Vérification manuelle recommandée |
| 50+ | SUSPICIOUS | Vérification manuelle obligatoire |

## Interfaces utilisateur

**CRM Fournisseurs** (`/`) — Vue métier regroupant les documents par fournisseur (SIRET). Affiche le cumul des montants validés et l'historique des documents par fournisseur.

**Outil de Conformité** (`/conformity`) — Interface de validation destinée aux équipes internes. Permet l'upload de documents, le déclenchement de l'analyse IA, la consultation des anomalies détectées et la gestion manuelle des statuts.

## Équipe

| Rôle | Nom | Dossier / Fichier |
|---|---|---|
| Scénario Maker | Omomene IWELOMEN | `dataset/` `generator.py` |
| Responsable OCR | Cleg LOUFOUA | `Cleg-partie_ocr/` |
| Responsable Front + API | Hyndi FANNIR | `backend/` `frontend/` |
| Chef BDD NoSQL | Mohammed MOSLEH | `database/` |
| Liaison API / BDD | Nassim BOUFALOUS | `backend/` `database/` |
| Anomaly Detector | Ikhlas LAGHMICH | `anomaly/` |
| Pipeline Engineer + Chef | Narcisse TSAFACK | `pipeline_airflow/` `Docker/` |

## Stack technique

| Composant | Technologie |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, Axios |
| Backend | Node.js, Express.js, Mongoose |
| Base de données | MongoDB 7.0, GridFS |
| OCR | EasyOCR, PyMuPDF, spaCy |
| Détection anomalies | Python pur, moteur de règles métier |
| Orchestration | Apache Airflow 2.9.1 |
| Conteneurisation | Docker, Docker Compose |

## Structure du projet

```
DocuMind/
├── generator.py              ← génération dataset (Omomene)
├── docker-compose.yml        ← orchestration Docker (Narcisse)
├── .env.example              ← template variables d'environnement
├── Docker/                   ← Dockerfiles par service (Narcisse)
│   ├── airflow/
│   ├── backend/
│   ├── frontend/
│   ├── anomaly/
│   └── ocr/
├── Cleg-partie_ocr/          ← module OCR (Cleg)
├── anomaly/                  ← moteur détection anomalies (Ikhlas)
├── backend/                  ← API Express (Hyndi + Nassim)
├── frontend/                 ← interface React (Hyndi)
├── database/                 ← modèles MongoDB + GridFS (Mohammed)
├── pipeline_airflow/         ← DAGs Airflow (Narcisse)
│   └── dags/
│       ├── dag_ingestion.py
│       ├── dag_traitement.py
│       ├── dag_validation.py
│       └── callbacks.py
└── dataset/                  ← documents de test (Omomene)
```

## Lancement

### Prérequis

- Docker Desktop installé et démarré
- Git

### Démarrage

```bash
git clone <url-du-repo>
cd DocuMind
cp .env.example .env
docker compose up -d
```

Docker démarre automatiquement tous les services et initialise Airflow au premier lancement.

### Vérification

```bash
docker compose ps
```

Tous les conteneurs doivent être en statut `running`.

## Accès aux services

| Service | URL | Login |
|---|---|---|
| Frontend CRM | http://localhost:5173 | — |
| Frontend Conformité | http://localhost:5173/conformity | — |
| Backend API | http://localhost:5000/api/documents | — |
| Airflow | http://localhost:8080 | admin / admin |
| MongoDB | localhost:27017 | admin / 2026 |

## Variables d'environnement

| Variable | Valeur par défaut | Description |
|---|---|---|
| `MONGO_ROOT_USER` | username | Utilisateur MongoDB |
| `MONGO_ROOT_PASSWORD` | password | Mot de passe MongoDB |
| `AIRFLOW_FERNET_KEY` | voir .env.example | Clé de chiffrement Airflow |

## Génération du dataset

`generator.py` génère 20 fournisseurs avec 5 documents chacun et des scénarios d'anomalies réalistes (SIRET incohérent, URSSAF expirée, montants différents, RIB incorrect). Utilisé uniquement par Omomene pour alimenter `dataset/`.

```bash
pip install faker jinja2 pdfkit pdf2image opencv-python
python generator.py
```

## Routes API

| Méthode | Route | Description |
|---|---|---|
| GET | `/api/documents` | Liste tous les documents |
| POST | `/api/documents/upload` | Upload un document (multipart/form-data) |
| PATCH | `/api/documents/:id` | Met à jour le statut et les données extraites |
| POST | `/api/documents/:id/analyze` | Déclenche l'analyse IA |