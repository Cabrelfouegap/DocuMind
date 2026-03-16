const mongoose = require('mongoose');

// Création du schéma pour la zone Curated (Données structurées et validées)
const curatedDocumentSchema = new mongoose.Schema({
  cleanDocumentId: { 
    type: mongoose.Schema.Types.ObjectId, 
    ref: 'CleanDocument', 
    required: true 
    // Lien vers le texte brut de la zone Clean
  },
  documentCategory: { 
    type: String, 
    enum: ['FACTURE', 'ATTESTATION_VIGILANCE', 'AUTRE'], 
    required: true 
    // Classification automatique du document
  },
  
  // Les informations métiers clés extraites par l'IA
  extractedData: {
    siret: { type: String },
    tva: { type: String },
    dateDocument: { type: Date },
    montantTotal: { type: Number }
  },

  // La section dédiée à la détection d'anomalies
  validation: {
    isValid: { 
      type: Boolean, 
      default: false 
      // Passe à true si aucune anomalie n'est détectée
    },
    anomaliesDetected: [{ 
      type: String 
      // Stocke les erreurs du type : "SIRET différent", "TVA incohérente", "Date expirée"
    }]
  }
}, { 
  timestamps: true 
});

module.exports = mongoose.model('CuratedDocument', curatedDocumentSchema);