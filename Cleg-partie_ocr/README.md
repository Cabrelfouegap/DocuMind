# 🔍 Module OCR — Hackathon IPSSI 2022

> **Rôle : Responsable OCR (M1)**  
> Extraction automatique de données à partir de documents administratifs (PDFs, scans, images dégradées).

---

## 📁 Structure du projet

```
ocr/
├── pipeline_ocr.py       # Point d'entrée — orchestre tout
├── extraction_texte.py   # Lecture PDF / image + OCR EasyOCR
├── nettoyage.py          # Nettoyage du texte brut
├── entites.py            # NER spaCy + regex (SIRET, TVA, dates…)
├── evaluation.py         # Métriques qualité OCR (CER / WER)
├── structuration.py      # Assemblage JSON final
├── requirements.txt      # Dépendances Python
├── tests/
│   └── test_pipeline.py  # Tests unitaires et de bout en bout
└── docs_test/            # Dossier pour tes documents de test (non versionné)
```

---

## ⚙️ Installation

### 1. Prérequis

- Python 3.9 ou plus
- pip

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Télécharger le modèle spaCy français

```bash
python -m spacy download fr_core_news_md
```

> Si la commande échoue (droits), essaie :
> ```bash
> python -m spacy download fr_core_news_sm
> ```

---

## 🚀 Utilisation

### Traiter un seul fichier

```bash
python pipeline_ocr.py ma_facture.pdf
python pipeline_ocr.py mon_scan.jpg
```

### Traiter un dossier entier

```bash
python pipeline_ocr.py mon_dossier_docs/
```

Les résultats JSON sont sauvegardés automatiquement dans `resultats_ocr/`.

---

## 🧪 Lancer les tests

```bash
python -m pytest tests/test_pipeline.py -v
```

---

## 📤 Format de sortie JSON

Chaque document traité produit un fichier JSON de cette forme :

```json
{
  "meta": {
    "nom_fichier": "facture.pdf",
    "type_document": "facture",
    "hash_md5": "a3f9...",
    "date_traitement": "2022-03-14T09:30:00"
  },
  "texte_brut": "...",
  "texte_propre": "...",
  "champs_admin": {
    "siret": ["12345678901234"],
    "tva_intra": ["FR12123456789"],
    "montants": ["1 250,00 €"],
    "dates": ["15/03/2022"],
    "emails": [],
    "telephones": []
  },
  "entites_ner": {
    "personnes": ["M. Dupont"],
    "organisations": ["Société Générale"],
    "lieux": ["Paris"]
  },
  "qualite_ocr": {
    "confiance_estimee_pct": 94.2,
    "mode": "estimation_heuristique"
  },
  "validation": {
    "statut": "en_attente",
    "anomalies": []
  }
}
```

---

## 🔗 Interfaces avec les autres modules

| Module | Ce qu'il reçoit de l'OCR |
|--------|--------------------------|
| **Chef BDD / Data Lake** | Le fichier JSON complet via `resultats_ocr/` |
| **Pipeline Engineer (Airflow)** | `pipeline_ocr.py` est appelé comme tâche dans un DAG |
| **Anomaly Detector** | Lit le bloc `champs_admin` et remplit `validation.anomalies` |
| **Responsable Front** | Consomme le JSON via l'API backend |

---

## 🛠️ Stack technique

| Outil | Usage |
|-------|-------|
| **EasyOCR** | Moteur OCR principal (images + PDFs scannés) |
| **PyMuPDF (fitz)** | Lecture PDF natif + conversion pages → images |
| **spaCy** | NER — détection personnes, organisations, lieux |
| **regex** | Extraction champs admin (SIRET, TVA, montants, dates) |
| **Levenshtein** | Calcul CER/WER pour évaluer la qualité OCR |
