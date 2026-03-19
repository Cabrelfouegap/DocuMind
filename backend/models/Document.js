const mongoose = require('mongoose');

const documentSchema = new mongoose.Schema({
  filename: {
    type: String,
    required: true
  },
  originalName: {
    type: String,
    required: true
  },
  path: {
    type: String,
    required: true
  },
  mimetype: {
    type: String,
    required: true
  },
  status: {
  type: String,
  enum: ['En attente', 'Conforme', 'Non conforme', 'Warning'],
  default: 'En attente'
  },
  reason: {
    type: String,
    default: ''
  },
  aiGenerated: {
    type: Boolean,
    default: false
  },
  type: {
    type: String,
    default: ''
  },
  extractedData: {
    siret: { type: String, default: '' },
    companyName: { type: String, default: '' },
    tvaNumber: { type: String, default: '' },
    amountHT: { type: Number, default: 0 },
    amountTTC: { type: Number, default: 0 },
    emissionDate: { type: String, default: '' },
    expirationDate: { type: String, default: '' },
    inconsistencyNote: { type: String, default: '' }
  }
}, {
  timestamps: true
});

const Document = mongoose.model('Document', documentSchema);

module.exports = Document;
