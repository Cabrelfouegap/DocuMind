const mongoose = require('mongoose');

const rawDocumentSchema = new mongoose.Schema(
  {
    originalFileName: {
      type: String,
      required: true,
    },
    storedFilePath: {
      type: String,
      required: true,
    },
    mimeType: {
      type: String,
      required: true,
    },
    processingStatus: {
      type: String,
      enum: ['PENDING', 'PROCESSING', 'OCR_COMPLETED', 'FAILED'],
      default: 'PENDING',
    },
    status: {
      type: String,
      enum: ['En attente', 'Conforme', 'Non conforme'],
      default: 'En attente',
    },
    reason: {
      type: String,
      default: '',
    },
    aiGenerated: {
      type: Boolean,
      default: false,
    },
    type: {
      type: String,
      default: '',
    },
    extractedData: {
      type: mongoose.Schema.Types.Mixed,
      default: {},
    },
  },
  {
    timestamps: true,
  }
);

const RawDocument = mongoose.model('RawDocument', rawDocumentSchema);

module.exports = RawDocument;
