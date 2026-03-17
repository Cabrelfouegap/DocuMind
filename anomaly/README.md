Ce projet implémente un moteur de détection d’anomalies pour des documents fournisseurs (devis, factures, URSSAF, KBIS, RIB) à partir de données structurées issues d’un pipeline data.


#  Objectif

Détecter automatiquement les incohérences et anomalies dans les documents fournisseurs afin de :

- améliorer la qualité des données
- sécuriser les processus métiers
- réduire les vérifications manuelles
- fournir un score de confiance et une décision automatique

---

#  Fonctionnement

Le module prend en entrée des documents structurés (zone Curated) regroupés par fournisseur (`vendorId`) et retourne un bloc de validation contenant :

- un score d’anomalie
- un statut (VALID / WARNING / SUSPICIOUS)
- une décision (automatique ou manuelle)
- la liste détaillée des anomalies détectées

---

#  Input attendu

```json
{
  "vendorId": "vendor_01",
  "documents": [
    {
      "_id": "doc_1",
      "vendorId": "vendor_01",
      "documentType": "invoice",
      "ocrConfidence": 0.95,
      "extractedData": {
        "company_name": "ABC SARL",
        "siret": "12345678900012",
        "total_ttc": 1200
      }
    }
  ]
}
```
---

#  Otput
```json
{
  "vendorId": "vendor_01",
  "validation": {
    "isValid": false,
    "ruleScoreRaw": 70,
    "ruleScoreNormalized": 46.67,
    "finalScore": 46.67,
    "status": "WARNING",
    "decision": "verification_manuelle",
    "anomalyCount": 3,
    "anomaliesDetected": [...],
    "lastCheckedAt": "2026-03-17T15:30:00+00:00",
    "engineVersion": "rule_based_v1"
  }
}
```

 # Règles implémentées

Le moteur repose sur des règles métier configurables :

 - Documents

Document manquant

Champs obligatoires manquants

- Qualité OCR

OCR confidence faible

 Cohérence entreprise

- SIRET mismatch

Nom entreprise incohérent

 - Finance

TVA incohérente

Écart devis / facture

 - Conformité

URSSAF expiré

- Bancaire

IBAN invalide

Titulaire RIB incohérent

- Global

Multiples signaux critiques


 # Scoring & décision

Le moteur calcule un score basé sur les anomalies détectées.

Score normalisé	Statut	Décision
0 – 19	VALID	Validation automatique
20 – 49	WARNING	Vérification manuelle
50+	SUSPICIOUS	Vérification manuelle

# Exécution
 Lancer le test
python test_detector.py