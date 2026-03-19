# DocuMind - Architecture Base de Données

**Projet :** DocuMind - Validation automatique de documents administratifs
**Auteur :** Mohammed MOSLEH, Chef BDD (Groupe 31)

Ce dossier contient l'infrastructure de stockage et la couche de persistance des données du projet DocuMind.

---

## Architecture Technique Détaillée

### A. Choix Technologique
L'architecture repose sur une pile **MERN** avec **MongoDB** comme moteur de base de données NoSQL. Ce choix permet une flexibilité totale pour stocker des documents aux structures variées (Quote, Invoice, URSSAF, Kbis, RIB) sans les contraintes de schéma d'une base SQL.

### B. Structuration du Data Lake en 3 Zones 
1. **Zone Raw (Brute) :** Utilisation de **MongoDB GridFS** pour le stockage physique des documents binaires (PDF, Scans). Les métadonnées sont indexées avec un statut `PENDING` pour l'orchestration via Airflow.
2. **Zone Clean (Nettoyée) :** Stockage du texte brut extrait par les moteurs OCR (Tesseract/EasyOCR). Chaque entrée est liée par un `ObjectId` au document Raw pour assurer la traçabilité.
3. **Zone Curated (Valorisée) :** Données hautement structurées au format JSON. Cette zone inclut les champs métiers extraits et un objet de validation gérant les anomalies détectées (ex: expiration de date, SIRET invalide).

### C. Sécurité et Industrialisation 
* **Sécurisation :** Mise en place du contrôle d'accès basé sur les rôles (**RBAC**). L'API et l'orchestrateur utilisent des identifiants restreints, isolés via des variables d'environnement (`.env`).
* **Disponibilité :** L'architecture est conçue pour le **stockage distribué** via des Replica Sets MongoDB, garantissant la résilience des données administratives sensibles.

---

## Fonctionnalités BDD

* **Architecture 3 Zones** : Séparation physique et logique des données (Raw, Clean, Curated).
* **Stockage Hybride** : Gestion des métadonnées (JSON) et des fichiers lourds (GridFS).
* **Sécurité** : Authentification MongoDB activée et protection des secrets via dotenv.
* **Flexibilité** : Support multi-documents (Factures, Kbis, RIB, etc.).

---

## Structure du projet

* `/config` : Configuration de la connexion MongoDB.
* `/models` : Schémas Mongoose (Raw, Clean, Curated).
* `/middlewares` : Gestion du Data Lake (GridFS/Multer).
* `server.js` : Point d'entrée de l'API backend.

---

## Installation et Test local

1. **Prérequis** :
   * Node.js installé.
   * MongoDB Compass lancé sur `localhost:27017`.

2. **Configuration** :
Créer un fichier .env à la racine du dossier.

Ajouter :

Bash
MONGO_URI=mongodb://USER:PASSWORD@localhost:27017/hackathon_ipssi?authSource=admin
(Remplacez USER et PASSWORD par vos identifiants personnels).

3. **Installation** :
   ```bash
   npm install
   

4. **Démarrage du serveur API** :
```bash
node server.js

```
