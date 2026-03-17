const mongoose = require('mongoose');

// Création du schéma pour la zone Clean (Résultat brut de l'OCR)
const cleanDocumentSchema = new mongoose.Schema({
  rawDocumentId: { 
    type: mongoose.Schema.Types.ObjectId, 
    ref: 'RawDocument', 
    required: true 
    // Lien relationnel direct vers le fichier physique de la zone Raw
  },
  extractedText: { 
    type: String, 
    required: true 
    // Le bloc de texte complet généré par l'IA
  },
  ocrEngineUsed: {
    type: String,
    enum: ['TESSERACT', 'EASYOCR', 'KERAS_OCR', 'OTHER'],
    default: 'TESSERACT'
    // Permet de tracer quelle technologie a été utilisée
  },
  confidenceScore: {
    type: Number,
    min: 0,
    max: 100
    // Un pourcentage évaluant le taux d'erreur de l'OCR
  }
}, { 
  timestamps: true 
});

module.exports = mongoose.model('CleanDocument', cleanDocumentSchema);