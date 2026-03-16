const mongoose = require('mongoose');

// Création du schéma pour la zone Raw (Données brutes en Ingestion)
const rawDocumentSchema = new mongoose.Schema({
  originalFileName: { 
    type: String, 
    required: true 
  },
  storedFilePath: { 
    type: String, 
    required: true 
    // C'est ici que tu stockeras le chemin local du scan ou du PDF
  },
  mimeType: { 
    type: String, 
    required: true 
    // Exemple : 'application/pdf', 'image/jpeg' ou 'image/png'
  },
  processingStatus: { 
    type: String, 
    enum: ['PENDING', 'PROCESSING', 'OCR_COMPLETED', 'FAILED'], 
    default: 'PENDING' 
    // Indispensable pour que Airflow sache quels documents traiter
  },
  uploadedAt: { 
    type: Date, 
    default: Date.now 
  }
}, { 
  // Ajoute automatiquement createdAt et updatedAt
  timestamps: true 
});

module.exports = mongoose.model('RawDocument', rawDocumentSchema);