const express = require('express');
const router = express.Router();
const RawDocument = require('../../database/models/RawDocument');
const uploadToDataLake = require('../middlewares/uploadInstance').get();
const { GridFSBucket } = require('mongodb');
const mongoose = require('mongoose');


// POST /upload
router.post('/upload', uploadToDataLake.array('files'), async (req, res) => {
  try {
    if (!req.files || req.files.length === 0) {
      return res.status(400).json({ success: false, message: "Aucun fichier n'a été reçu." });
    }

    const resultats = [];

    for (const file of req.files) {
      const newRawDocument = new RawDocument({
        originalFileName: file.originalname,
        storedFilePath: file.filename,
        mimeType: file.mimetype,
        processingStatus: 'PENDING'
      });

      const savedDoc = await newRawDocument.save();
      resultats.push(savedDoc);
    }

    res.status(201).json({
      success: true,
      message: 'Documents stockés avec succès dans le Data Lake',
      data: resultats
    });

  } catch (error) {
    console.error("Erreur lors de l'upload :", error);
    res.status(500).json({
      success: false,
      message: "Erreur interne du serveur lors de la sauvegarde"
    });
  }
});


// GET /
router.get('/', async (req, res) => {
  try {
    const documents = await RawDocument.find().sort({ createdAt: -1 });
    res.json(documents);
  } catch (error) {
    console.error('Erreur lors de la récupération :', error);
    res.status(500).json({
      success: false,
      message: 'Erreur interne du serveur'
    });
  }
});


// PATCH /:id
router.patch('/:id', async (req, res) => {
  try {
    const { processingStatus } = req.body;

    const docModifie = await RawDocument.findByIdAndUpdate(
      req.params.id,
      { processingStatus },
      { new: true, runValidators: true }
    );

    if (!docModifie) {
      return res.status(404).json({
        success: false,
        message: 'Document introuvable'
      });
    }

    res.json(docModifie);

  } catch (error) {
    console.error('Erreur lors de la mise à jour :', error);
    res.status(500).json({
      success: false,
      message: 'Erreur interne du serveur'
    });
  }
});


// POST /:id/analyze
router.post('/:id/analyze', async (req, res) => {
  try {
    const document = await RawDocument.findById(req.params.id);

    if (!document) {
      return res.status(404).json({
        success: false,
        message: 'Document introuvable'
      });
    }

    const nomFichier = document.originalFileName.toLowerCase();
    const estImage = ['image/png', 'image/jpeg'].includes(document.mimeType);
    const estWord = [
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ].includes(document.mimeType);

    let typeSuggere = 'Autre';
    if (nomFichier.includes('facture'))         typeSuggere = 'Facture';
    else if (nomFichier.includes('invoice'))    typeSuggere = 'Facture';
    else if (nomFichier.includes('devis'))      typeSuggere = 'Devis';
    else if (nomFichier.includes('quote'))      typeSuggere = 'Devis';
    else if (nomFichier.includes('contrat'))    typeSuggere = 'Contrat';
    else if (nomFichier.includes('kbis'))       typeSuggere = 'Kbis';
    else if (nomFichier.includes('urssaf'))     typeSuggere = 'Urssaf';
    else if (nomFichier.includes('rib'))        typeSuggere = 'RIB';
    else if (estImage)                          typeSuggere = 'Identité';

    let nouveauStatut = 'PROCESSING';
    if (estWord) nouveauStatut = 'FAILED';

    const docFinal = await RawDocument.findByIdAndUpdate(
      req.params.id,
      { processingStatus: nouveauStatut },
      { new: true }
    );

    res.json({ ...docFinal.toObject(), typeSuggere });

  } catch (error) {
    console.error("Erreur lors de l'analyse :", error);
    res.status(500).json({
      success: false,
      message: "Erreur interne du serveur lors de l'analyse"
    });
  }
});

router.get('/file/:filename', async (req, res) => {
  try {
    const bucket = new GridFSBucket(mongoose.connection.db, { bucketName: 'datalake_raw' });
    const stream = bucket.openDownloadStreamByName(req.params.filename);
    stream.on('error', () => res.status(404).json({ message: 'Fichier introuvable' }));
    stream.pipe(res);
  } catch (error) {
    res.status(500).json({ message: 'Erreur serveur' });
  }
});


module.exports = router;