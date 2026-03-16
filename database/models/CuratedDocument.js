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
  
  // Utilisation de Mixed pour accepter les différentes structures (Devis vs URSSAF vs RIB)
  // L'IA insérera ici soit les champs du Quote, soit ceux du Kbis, etc.
  extractedData: { 
    type: mongoose.Schema.Types.Mixed 
  },

  // La section pour l'Anomaly Detector
  validation: {
    isValid: { 
      type: Boolean, 
      default: false 
    },
    // Préparation pour les scénarios d'erreurs de l'équipe
    anomaliesDetected: [{ 
      type: String 
      // Exemples prévus par l'équipe : "Expired URSSAF", "SIRET mismatch", "Price mismatch", "RIB mismatch"
    }]
  }
}, { 
  timestamps: true 
});

module.exports = mongoose.model('CuratedDocument', curatedDocumentSchema);