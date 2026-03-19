const express = require('express');
const router = express.Router();
const upload = require('../config/multer');
const Document = require('../models/Document');
const mongoose = require('mongoose');
const fs = require('fs');
const { GridFSBucket, ObjectId } = require('mongodb');

const parseAmount = (rawValue) => {
  if (rawValue === null || rawValue === undefined) return 0;
  if (typeof rawValue === 'number') return Number.isFinite(rawValue) ? rawValue : 0;

  let text = String(rawValue).trim();
  if (!text) return 0;

  text = text.replace(/[^\d,.\-]/g, '');

  if (text.includes(',') && text.includes('.')) {
    text = text.replace(/,/g, '');
  } else if (text.includes(',')) {
    text = text.replace(',', '.');
  }

  const amount = Number.parseFloat(text);
  return Number.isFinite(amount) ? amount : 0;
};

router.post('/upload', upload.array('files'), async (req, res) => {
  if (!req.files || req.files.length === 0) {
    return res.status(400).json({
      message: 'Aucun fichier fourni'
    });
  }

  const resultats = [];
  const vendorIdSession = `UPLOAD_${Date.now()}`;
  const db = mongoose.connection.db;
  const bucket = new GridFSBucket(db, { bucketName: 'datalake_raw' });
  const rawDocumentsCollection = db.collection('rawdocuments');

  for (let i = 0; i < req.files.length; i++) {
    const file = req.files[i];
    const rawDocId = new ObjectId();    
    const buffer = await fs.promises.readFile(file.path);

    await new Promise((resolve, reject) => {
      const uploadStream = bucket.openUploadStream(file.filename, {
        contentType: file.mimetype,
      });
      uploadStream.end(buffer);
      uploadStream.once('finish', resolve);
      uploadStream.once('error', reject);
    });

    await rawDocumentsCollection.insertOne({
      _id: rawDocId,
      originalFileName: file.originalname,
      storedFilePath: file.filename,
      vendorId: vendorIdSession,
      processingStatus: 'PENDING',
    });

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
    amountHT: parseAmount(amountHT),
    amountTTC: parseAmount(amountTTC),
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
  const docFinal = await Document.findByIdAndUpdate(
    idDocument,
    {
      status: 'En attente',
      reason: 'Traitement OCR + validation déclenchés (Airflow).',
      aiGenerated: false
    },
    { new: true }
  );  
  try {
    await mongoose.connection.db.collection('rawdocuments').updateOne(
      { _id: new ObjectId(idDocument) },
      { $set: { processingStatus: 'PENDING' } }
    );
  } catch (_e) {
  }  
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
  }

  res.json(docFinal);
});

module.exports = router;

