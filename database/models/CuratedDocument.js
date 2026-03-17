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

  // Le bloc validation enrichi suite à la demande de l'équipe IA
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
    
    // Modification : Tableau d'objets structurés au lieu de simples chaînes
    anomaliesDetected: [{ 
      anomalyCode: { type: String },
      severity: { type: String }, // Ex: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
      score: { type: Number },
      message: { type: String },
      details: { type: mongoose.Schema.Types.Mixed } // Mixed permet à l'IA d'y mettre ce qu'elle veut (ex: les valeurs attendues vs trouvées)
    }]
  }
}, { 
  timestamps: true 
});

module.exports = mongoose.model('CuratedDocument', curatedDocumentSchema);