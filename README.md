# DocuMind - Hackathon 2026 Edition

DocuMind est une plateforme intelligente de gestion de documents fournisseurs, conçue pour répondre aux exigences du **Hackathon 2026**. Elle intègre une architecture de données en 3 zones et une double interface utilisateur pour maximiser l'efficacité opérationnelle.

## Architecture du Projet

Le projet suit une stratégie de stockage et de traitement en 3 zones distinctes :

1.  **Zone Raw (Brute)** : Stockage des fichiers originaux (PDF, Images, Word) tels qu'ils sont téléchargés par l'utilisateur.
2.  **Zone Clean (Propre)** : Documents classés par type (Facture, Devis, Contrat, Identité) après un premier passage de détection.
3.  **Zone Curated (Organisée)** : Données métier structurées extraites (SIRET, Numéro de TVA, Montants HT/TTC, Dates) et enregistrées directement en base de données pour une exploitation immédiate dans le CRM.

### Interfaces Utilisateur (Dual Front-end)

-   **CRM Fournisseurs** (`/`) : Une vue métier centrée sur les fournisseurs. Elle regroupe les documents par SIRET et affiche le cumul des montants validés. C'est ici que l'on consulte la "Donnée Or".
-   **Outil de Conformité** (`/conformity`) : Une interface haute densité destinée aux équipes de validation. Elle permet l'upload massif, l'analyse IA en un clic, et la gestion des motifs de refus ou d'incohérence.

## Configuration Technique

-   **Frontend** : React.js, Tailwind CSS, Axios.
-   **Backend** : Node.js, Express.js.
-   **Base de données** : MongoDB (via Mongoose).
-   **Gestion Fichiers** : Multer.

### Ports par défaut
- **Backend (Express)** : `5000`
- **Frontend (Vite)** : `5173`
- **Database (MongoDB)** : `27017`

### Routes API (Backend)
Toutes les routes API sont préfixées par `/api`.

- `GET /api/documents` : Récupère la liste de tous les documents.
- `POST /api/documents/upload` : Upload un ou plusieurs nouveaux documents (form-data).
- `PATCH /api/documents/:id` : Met à jour le statut, le motif ou l'origine (IA/Manuel).
- `POST /api/documents/:id/analyze` : Lance l'analyse OCR et la détection d'incohérences via IA.

**Fichiers Statiques** :
- `GET /uploads/:filename` : Accès direct aux fichiers sauvegardés sur le serveur.

### Variables d'Environnement (Backend)
Créez un fichier `.env` dans le dossier `backend` :

- `PORT` : Le port sur lequel le serveur Express s'exécute (ex: 5000).
- `MONGO_URI` : La chaîne de connexion MongoDB (ex: mongodb://localhost:27017/documind).

## Installation et Lancement

### Pré-requis
- Node.js (v18+)
- MongoDB (Running locally or via Atlas)

### 1. Configuration du Backend
```bash
cd backend
npm install
# Créez un fichier .env avec :
# PORT=5000
# MONGO_URI=mongodb://localhost:27017/documind
npm run dev
```

### 2. Configuration du Frontend
```bash
cd frontend
npm install
npm run dev
```
L'application sera accessible sur `http://localhost:5173`.

### 3. Initialisation des données (Optionnel)
Pour tester l'application avec des données de démonstration :
```bash
cd backend
node seed.js
```

## Docker (À venir)
Le projet contient un fichier `docker-compose.yml` (en cours de configuration) qui permettra de lancer l'ensemble de la stack (Frontend, Backend, MongoDB) avec une seule commande.
