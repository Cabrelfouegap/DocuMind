const express = require('express');
const router = express.Router();
const upload = require('../config/multer');
const Document = require('../models/Document');

router.post('/upload', upload.array('files'), async (req, res) => {
  if (!req.files || req.files.length === 0) {
    return res.status(400).json({
      message: 'Aucun fichier fourni'
    });
  }

  const resultats = [];

  for (let i = 0; i < req.files.length; i++) {
    const file = req.files[i];
    const newDoc = await Document.create({
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

  const estImage = (document.mimetype === 'image/png' || document.mimetype === 'image/jpeg');
  const estWord = (document.mimetype === 'application/msword' || document.mimetype === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document');

  let statutSuggere = 'Conforme';
  let motifSuggere = '';
  let typeSuggere = 'Autre';

  const nomFichier = document.originalName.toLowerCase();

  const existing = document.extractedData || {};
  const bodyData = (req.body && req.body.extractedData) ? req.body.extractedData : {};

  const companyName =
    bodyData.companyName ?? bodyData.company_name ?? existing.companyName ?? existing.company_name ?? '';
  const amountHT =
    bodyData.amountHT ?? bodyData.amount_ht ?? existing.amountHT ?? existing.amount_ht ?? 0;
  const amountTTC =
    bodyData.amountTTC ?? bodyData.total_ttc ?? existing.amountTTC ?? existing.total_ttc ?? 0;
  const tvaNumber =
    bodyData.tvaNumber ?? bodyData.vat_number ?? existing.tvaNumber ?? existing.vat_number ?? '';
  const emissionDate =
    bodyData.emissionDate ?? bodyData.invoice_issue_date ?? bodyData.issue_date ??
    existing.emissionDate ?? existing.invoice_issue_date ?? existing.issue_date ?? '';
  const expirationDate =
    bodyData.expirationDate ?? bodyData.expiration_date ??
    existing.expirationDate ?? existing.expiration_date ?? '';

  const donneesExtraites = {
    siret: bodyData.siret ?? existing.siret ?? '',
    companyName,
    tvaNumber,
    amountHT: Number(amountHT) || 0,
    amountTTC: Number(amountTTC) || 0,
    emissionDate,
    expirationDate,
    inconsistencyNote: bodyData.inconsistencyNote ?? existing.inconsistencyNote ?? ''
  };

  if (nomFichier.includes('facture') || nomFichier.includes('invoice')) {
    typeSuggere = 'Facture';
  } else if (nomFichier.includes('kbis')) {
    typeSuggere = 'KBIS';
  } else if (nomFichier.includes('rib')) {
    typeSuggere = 'RIB';
  } else if (nomFichier.includes('urssaf')) {
    typeSuggere = 'URSSAF';
  } else if (nomFichier.includes('devis') || nomFichier.includes('quote')) {
    typeSuggere = 'Devis';
  } else if (estImage) {
    typeSuggere = 'Identité';
  }

  if (estWord) {
    statutSuggere = 'Non conforme';
    motifSuggere = 'Signature ou données obligatoires manquantes (détecté par IA).';
  }

  const docFinal = await Document.findByIdAndUpdate(
    idDocument,
    {
      status: statutSuggere,
      reason: motifSuggere,
      aiGenerated: true,
      type: typeSuggere,
      extractedData: donneesExtraites
    },
    { new: true }
  );

  res.json(docFinal);
});

module.exports = router;

