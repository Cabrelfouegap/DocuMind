const mongoose = require('mongoose');

const curatedDocumentSchema = new mongoose.Schema({
  cleanDocumentId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'CleanDocument',
    required: true
  },
  vendorId: {
    type: String,
    required: true
  },
  documentType: {
    type: String,
    enum: ['quote', 'invoice', 'urssaf', 'kbis', 'rib'],
    required: true
  },
  extractedData: {
    type: mongoose.Schema.Types.Mixed
  },
  validation: {
    isValid: { type: Boolean, default: false },
    ruleScoreRaw: { type: Number },
    ruleScoreNormalized: { type: Number },
    finalScore: { type: Number },
    status: { type: String },
    decision: { type: String },
    anomalyCount: { type: Number, default: 0 },
    lastCheckedAt: { type: Date },
    engineVersion: { type: String },
    anomaliesDetected: [{
      anomalyCode: { type: String },
      severity: { type: String },
      score: { type: Number },
      message: { type: String },
      details: { type: mongoose.Schema.Types.Mixed }
    }]
  }
}, {
  timestamps: true
});

module.exports = mongoose.model('CuratedDocument', curatedDocumentSchema);

