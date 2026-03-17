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

## Stack Technique

-   **Frontend** : React.js, Tailwind CSS, Axios.
-   **Backend** : Node.js, Express.js.
-   **Base de données** : MongoDB (via Mongoose).
-   **Gestion Fichiers** : Multer.

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
