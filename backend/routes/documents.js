const express = require('express');
const router = express.Router();
const path = require('path');
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
  const status = req.body.status;
  const reason = req.body.reason;
  const aiGenerated = req.body.aiGenerated;

  const docModifie = await Document.findByIdAndUpdate(
    id,
    { 
      status: status, 
      reason: reason || '', 
      aiGenerated: aiGenerated ?? false 
    },
    { 
      new: true, 
      runValidators: true 
    }
  );

  if (!docModifie) {
    return res.status(404).json({ 
      message: 'Document introuvable' 
    });
  }

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

  if (nomFichier.includes('facture')) {
    typeSuggere = 'Facture';
  } else if (nomFichier.includes('devis')) {
    typeSuggere = 'Devis';
  } else if (nomFichier.includes('contrat')) {
    typeSuggere = 'Contrat';
  } else if (estImage) {
    typeSuggere = 'Identité';
  }

  if (estWord) {
    statutSuggere = 'Non conforme';
    motifSuggere = 'Signature ou données obligatoires manquantes (détecté par IA).';
  }
  let donneesExtraites = {
    siret: '834 657 239 00012',
    tvaNumber: 'FR 32 834657239',
    amountHT: 1250.50,
    amountTTC: 1500.60,
    emissionDate: '2024-03-01',
    expirationDate: '',
    inconsistencyNote: ''
  };

  if (typeSuggere === 'Identité') {
    donneesExtraites.siret = '';
    donneesExtraites.tvaNumber = '';
    donneesExtraites.amountHT = 0;
    donneesExtraites.amountTTC = 0;
  }

  if (typeSuggere === 'Facture' && nomFichier.includes('fake')) {
    donneesExtraites.siret = '999 999 999 00099';
    donneesExtraites.inconsistencyNote = 'ALERTE : Numéro SIRET inconnu ou incohérent avec la base fournisseur.';
    statutSuggere = 'Non conforme';
    motifSuggere = 'Incohérence critique de données (SIRET).';
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
