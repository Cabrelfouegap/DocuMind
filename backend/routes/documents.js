const express = require('express');
const router = express.Router();
const path = require('path');
const upload = require('../config/multer');
const RawDocument = require('../models/RawDocument');
const { envoyerFichierDansGridFS } = require('../config/gridfs');

router.post('/upload', upload.array('files'), async (req, res) => {
  if (!req.files || req.files.length === 0) {
    return res.status(400).json({ message: 'Aucun fichier fourni' });
  }

  const resultats = [];

  for (let i = 0; i < req.files.length; i++) {
    const file = req.files[i];
    try {
      await envoyerFichierDansGridFS(file.path, file.path);
    } catch (errGridFS) {
      console.error('GridFS upload raté pour', file.originalname, errGridFS.message);
    }

    // On détermine un type initial à partir du nom de fichier
    const nomFichier = file.originalname.toLowerCase();
    const mime = file.mimetype || '';
    let typeInitial = '';
    const estImage = (mime === 'image/png' || mime === 'image/jpeg');

    if (nomFichier.includes('invoice') || nomFichier.includes('facture')) {
      typeInitial = 'invoice';
    } else if (nomFichier.includes('quote') || nomFichier.includes('devis')) {
      typeInitial = 'quote';
    } else if (nomFichier.includes('urssaf') || nomFichier.includes('vigilance')) {
      typeInitial = 'urssaf';
    } else if (nomFichier.includes('kbis')) {
      typeInitial = 'kbis';
    } else if (nomFichier.includes('rib')) {
      typeInitial = 'rib';
    } else if (nomFichier.includes('contrat')) {
      typeInitial = 'contrat';
    } else if (estImage) {
      typeInitial = 'Identité';
    }

    const nouveauDoc = await RawDocument.create({
      originalFileName: file.originalname,
      storedFilePath: file.path,
      mimeType: file.mimetype,
      processingStatus: 'PENDING',
      status: 'En attente',
      type: typeInitial,
    });

    resultats.push(formaterPourFrontend(nouveauDoc));
  }

  res.status(201).json(resultats);
});

router.get('/', async (req, res) => {
  const docs = await RawDocument.find().sort({ createdAt: -1 });
  const docsFrontend = docs.map(formaterPourFrontend);
  res.json(docsFrontend);
});

router.patch('/:id', async (req, res) => {
  const id = req.params.id;
  const status = req.body.status;
  const reason = req.body.reason;
  const aiGenerated = req.body.aiGenerated;
  const extractedData = req.body.extractedData;

  const miseAJour = {};
  if (status !== undefined) miseAJour.status = status;
  if (reason !== undefined) miseAJour.reason = reason;
  if (aiGenerated !== undefined) miseAJour.aiGenerated = aiGenerated;
  if (extractedData !== undefined) miseAJour.extractedData = extractedData;

  if (aiGenerated === true) {
    miseAJour.processingStatus = 'OCR_COMPLETED';
  }

  const docModifie = await RawDocument.findByIdAndUpdate(
    id,
    { $set: miseAJour },
    { new: true, runValidators: true }
  );

  if (!docModifie) {
    return res.status(404).json({ message: 'Document introuvable' });
  }

  res.json(formaterPourFrontend(docModifie));
});

router.post('/:id/analyze', async (req, res) => {
  const idDocument = req.params.id;
  const document = await RawDocument.findById(idDocument);

  if (!document) {
    return res.status(404).json({ message: 'Document introuvable' });
  }

  const docFinal = await RawDocument.findByIdAndUpdate(
    idDocument,
    {
      $set: {
        status: 'En attente',
        reason: 'En attente de traitement Airflow/OCR.',
        aiGenerated: false,
        processingStatus: 'PENDING'
      }
    },
    { new: true }
  );

  res.json(formaterPourFrontend(docFinal));
});

const formaterPourFrontend = (doc) => {
  const objet = doc.toObject ? doc.toObject() : doc;

  const nomFichier = objet.storedFilePath 
    ? objet.storedFilePath.split('\\').pop().split('/').pop() 
    : '';

  return {
    _id: objet._id,
    originalName: objet.originalFileName,
    filename: nomFichier,
    mimetype: objet.mimeType,
    status: objet.status || 'En attente',
    reason: objet.reason || '',
    aiGenerated: objet.aiGenerated || false,
    type: objet.type || '',
    extractedData: objet.extractedData || {},
    processingStatus: objet.processingStatus,
    createdAt: objet.createdAt,
    updatedAt: objet.updatedAt
  };
};

module.exports = router;
