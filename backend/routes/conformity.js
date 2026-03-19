const express = require('express');
const router = express.Router();

// Modèle Mongoose (dupliqué côté backend pour être disponible dans l'image Docker)
const CuratedDocument = require('../models/CuratedDocument');

// Résumé des anomalies par fournisseur (key = SIRET)
router.get('/suppliers', async (_req, res) => {
  try {
    const rows = await CuratedDocument.aggregate([
      {
        $match: {
          'extractedData.siret': { $exists: true, $ne: '', $ne: null },
        },
      },
      {
        $group: {
          _id: '$extractedData.siret',
          companyName: { $first: '$extractedData.company_name' },
          status: { $first: '$validation.status' },
          finalScore: { $first: '$validation.finalScore' },
          anomalyCount: { $first: '$validation.anomalyCount' },
          docCount: { $sum: 1 },
          vendorIds: { $addToSet: '$vendorId' },
          documentTypes: { $addToSet: '$documentType' },
        },
      },
      { $sort: { finalScore: -1 } },
    ]);

    res.json(
      rows.map((r) => ({
        siret: r._id,
        companyName: r.companyName || '',
        status: r.status || 'UNKNOWN',
        finalScore: r.finalScore ?? 0,
        anomalyCount: r.anomalyCount ?? 0,
        docCount: r.docCount ?? 0,
        vendorIds: r.vendorIds || [],
        documentTypes: r.documentTypes || [],
      }))
    );
  } catch (err) {
    res.status(500).json({
      message: 'Erreur chargement anomalies fournisseurs',
      details: String(err?.message || err),
    });
  }
});

// Détails d’un fournisseur (documents + anomalies)
router.get('/suppliers/:siret', async (req, res) => {
  try {
    const { siret } = req.params;

    const docs = await CuratedDocument.find({ 'extractedData.siret': siret })
      .select('vendorId documentType extractedData validation')
      .sort({ createdAt: -1 })
      .lean();

    if (!docs || docs.length === 0) {
      return res.status(404).json({ message: 'Fournisseur introuvable', siret });
    }

    const first = docs[0] || {};
    res.json({
      siret,
      vendorId: first.vendorId,
      companyName: first.extractedData?.company_name || first.extractedData?.companyName || '',
      status: first.validation?.status || 'UNKNOWN',
      finalScore: first.validation?.finalScore ?? 0,
      anomalyCount: first.validation?.anomalyCount ?? 0,
      documents: docs.map((d) => ({
        documentType: d.documentType,
        extractedData: d.extractedData,
        validation: d.validation,
      })),
    });
  } catch (err) {
    res.status(500).json({
      message: 'Erreur chargement détails anomalies fournisseur',
      details: String(err?.message || err),
    });
  }
});

module.exports = router;

