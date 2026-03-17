const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env') });
const mongoose = require('mongoose');
const Document = require('./models/Document');

const mockDocs = [
  {
    filename: 'mock-attente-1.pdf',
    originalName: 'Contrat_prestation_2024.pdf',
    path: 'uploads/mock-attente-1.pdf',
    mimetype: 'application/pdf',
    status: 'En attente',
    reason: '',
  },
  {
    filename: 'mock-attente-2.docx',
    originalName: 'Rapport_mensuel_mars.docx',
    path: 'uploads/mock-attente-2.docx',
    mimetype: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    status: 'En attente',
    reason: '',
  },
  {
    filename: 'mock-conforme-1.pdf',
    originalName: 'Facture_fournisseur_001.pdf',
    path: 'uploads/mock-conforme-1.pdf',
    mimetype: 'application/pdf',
    status: 'Conforme',
    reason: '',
    aiGenerated: true,
    type: 'Facture',
    extractedData: {
      siret: '834 657 239 00012',
      tvaNumber: 'FR 32 834657239',
      amountHT: 1250.00,
      amountTTC: 1500.00,
      emissionDate: '2024-02-15',
      expirationDate: '',
      inconsistencyNote: ''
    }
  },
  {
    filename: 'mock-conforme-2.pdf',
    originalName: 'Attestation_vigilance.pdf',
    path: 'uploads/mock-conforme-2.pdf',
    mimetype: 'application/pdf',
    status: 'Conforme',
    reason: '',
    aiGenerated: true,
    type: 'Attestation',
    extractedData: {
      siret: '834 657 239 00012',
      tvaNumber: '',
      amountHT: 0,
      amountTTC: 0,
      emissionDate: '2024-01-10',
      expirationDate: '2024-07-10',
      inconsistencyNote: ''
    }
  },
  {
    filename: 'mock-nonconforme-1.pdf',
    originalName: 'Facture_Fake_Company.pdf',
    path: 'uploads/mock-nonconforme-1.pdf',
    mimetype: 'application/pdf',
    status: 'Non conforme',
    reason: 'Incohérence critique de données (SIRET).',
    aiGenerated: true,
    type: 'Facture',
    extractedData: {
      siret: '999 999 999 00099',
      tvaNumber: 'FR 00 000000000',
      amountHT: 50.00,
      amountTTC: 60.00,
      emissionDate: '2024-03-10',
      expirationDate: '',
      inconsistencyNote: 'ALERTE : Numéro SIRET inconnu ou incohérent avec la base fournisseur.'
    }
  },
];

const seed = async () => {
  await mongoose.connect(process.env.MONGO_URI);

  await Document.deleteMany({ filename: /^mock-/ });

  const inserted = await Document.insertMany(mockDocs);

  await mongoose.disconnect();
};

seed().catch((err) => {
  process.exit(1);
});
