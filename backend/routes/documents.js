const express = require('express');
const router = express.Router();
const upload = require('../config/multer');
const Document = require('../models/Document');
const mongoose = require('mongoose');
const fs = require('fs');
const { GridFSBucket, ObjectId } = require('mongodb');

router.post('/upload', upload.array('files'), async (req, res) => {
  if (!req.files || req.files.length === 0) {
    return res.status(400).json({
      message: 'Aucun fichier fourni'
    });
  }

  const resultats = [];
  const vendorIdSession = `UPLOAD_${Date.now()}`;

  // Zone Raw pour Airflow (rawdocuments + GridFS)
  const db = mongoose.connection.db;
  const bucket = new GridFSBucket(db, { bucketName: 'datalake_raw' });
  const rawDocumentsCollection = db.collection('rawdocuments');

  for (let i = 0; i < req.files.length; i++) {
    const file = req.files[i];

    // _id Mongo commun entre rawdocuments et Document backend.
    const rawDocId = new ObjectId();

    // 1) GridFS brut : le pipeline OCR retrouvera le fichier via storedFilePath (= filename GridFS)
    const buffer = await fs.promises.readFile(file.path);
    await new Promise((resolve, reject) => {
      const uploadStream = bucket.openUploadStream(file.filename, {
        contentType: file.mimetype,
      });
      uploadStream.end(buffer);
      uploadStream.once('finish', resolve);
      uploadStream.once('error', reject);
    });

    // 2) Insertion rawdocument (pour que dag_ingestion => dag_traitement => dag_validation s'exécute)
    await rawDocumentsCollection.insertOne({
      _id: rawDocId,
      originalFileName: file.originalname,
      storedFilePath: file.filename,
      vendorId: vendorIdSession,
      processingStatus: 'PENDING',
    });

    // 3) Document UX (créé avec le même _id pour que dag_validation puisse patcher /api/documents/:id)
    const newDoc = await Document.create({
      _id: rawDocId,
      filename: file.filename,
      originalName: file.originalname,
      path: file.path,
      mimetype: file.mimetype,
    });

    resultats.push(newDoc);
  }

  res.status(201).json(resultats);
});

router.get('/', async (req, res) => {
  const documents = await Document.find().sort({ createdAt: -1 });
  res.json(documents);
});

router.patch('/:id', async (req, res) => {
  const id = req.params.id;

  const existing = await Document.findById(id);
  if (!existing) {
    return res.status(404).json({
      message: 'Document introuvable'
    });
  }

  const {
    status,
    reason,
    aiGenerated,
    type,
    extractedData: incomingExtractedData = {}
  } = req.body || {};

  const current = existing.extractedData || {};
  const e = incomingExtractedData || {};

  const companyName =
    e.companyName ?? e.company_name ?? current.companyName ?? current.company_name ?? '';
  const amountHT =
    e.amountHT ?? e.amount_ht ?? current.amountHT ?? current.amount_ht ?? 0;
  const amountTTC =
    e.amountTTC ?? e.total_ttc ?? e.amount_ttc ?? current.amountTTC ?? current.total_ttc ?? 0;
  const tvaNumber =
    e.tvaNumber ?? e.vat_number ?? current.tvaNumber ?? current.vat_number ?? '';
  const emissionDate =
    e.emissionDate ?? e.invoice_issue_date ?? e.issue_date ??
    current.emissionDate ?? current.invoice_issue_date ?? current.issue_date ?? '';
  const expirationDate =
    e.expirationDate ?? e.expiration_date ??
    current.expirationDate ?? current.expiration_date ?? '';

  const mergedExtracted = {
    siret: e.siret ?? current.siret ?? '',
    companyName,
    tvaNumber,
    amountHT: Number(amountHT) || 0,
    amountTTC: Number(amountTTC) || 0,
    emissionDate,
    expirationDate,
    inconsistencyNote: e.inconsistencyNote ?? current.inconsistencyNote ?? ''
  };

  const update = {
    extractedData: mergedExtracted
  };

  if (typeof status === 'string') {
    update.status = status;
  }
  if (typeof reason === 'string') {
    update.reason = reason;
  }
  if (typeof aiGenerated === 'boolean') {
    update.aiGenerated = aiGenerated;
  }
  if (typeof type === 'string') {
    update.type = type;
  }

  const docModifie = await Document.findByIdAndUpdate(
    id,
    update,
    {
      new: true,
      runValidators: true
    }
  );

  res.json(docModifie);
});

router.post('/:id/analyze', async (req, res) => {
  const idDocument = req.params.id;

  const document = await Document.findById(idDocument);

  if (!document) {
    return res.status(404).json({
      message: 'Document introuvable'
    });
  }

  // Non destructif : on ne doit pas forcer "Conforme" sans passer par Airflow.
  const docFinal = await Document.findByIdAndUpdate(
    idDocument,
    {
      status: 'En attente',
      reason: 'Traitement OCR + validation déclenchés (Airflow).',
      aiGenerated: false
    },
    { new: true }
  );

  // Best-effort : marquer le rawdocument en PENDING (au cas où)
  try {
    await mongoose.connection.db.collection('rawdocuments').updateOne(
      { _id: new ObjectId(idDocument) },
      { $set: { processingStatus: 'PENDING' } }
    );
  } catch (_e) {
    // ignore
  }

  // Best-effort : déclencher un run de dag_ingestion pour démarrer rapidement.
  try {
    const airflowBaseUrl = process.env.AIRFLOW_BASE_URL || 'http://airflow-webserver:8080';
    const url = `${airflowBaseUrl}/api/v1/dags/dag_ingestion/dagRuns`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 3000);
    await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
      signal: controller.signal,
    }).catch(() => {});
    clearTimeout(timer);
  } catch (_e) {
    // ignore
  }

  res.json(docFinal);
});

module.exports = router;

