const express = require('express');
const router = express.Router();

const CuratedDocument = require('../models/CuratedDocument');

const normalizeAmount = (rawValue) => {
  if (rawValue === null || rawValue === undefined) return 0;
  if (typeof rawValue === 'number') return Number.isFinite(rawValue) ? rawValue : 0;

  let text = String(rawValue).trim();
  if (!text) return 0;
  text = text.replace(/[^\d,.\-]/g, '');

  if (text.includes(',') && text.includes('.')) {
    text = text.replace(/,/g, '');
  } else if (text.includes(',')) {
    text = text.replace(',', '.');
  }

  const n = Number.parseFloat(text);
  return Number.isFinite(n) ? n : 0;
};

const extractFinancialAmount = (doc) => {
  const e = doc?.extractedData || {};
  const candidates = [
    e.amountHT,
    e.amount_ht,
    e.total_ht,
    e.totalHT,
    e.montantHT,
    e.montant_ht,
    e.ht,
    e.amountTTC,
    e.amount_ttc,
    e.total_ttc,
    e.totalTTC,
    e.montantTTC,
    e.montant_ttc,
    e.ttc,
    e.total,
    e.amount,
  ];

  for (let i = 0; i < candidates.length; i++) {
    const amount = normalizeAmount(candidates[i]);
    if (amount !== 0) return amount;
  }

  const anomalies = doc?.validation?.anomaliesDetected || [];
  for (let i = 0; i < anomalies.length; i++) {
    const details = anomalies[i]?.details || {};
    const fallbackCandidates = [
      details.amountHt,
      details.amountHT,
      details.quoteTotalHt,
      details.invoiceTotalHt,
      details.quoteTotalTtc,
      details.invoiceTotalTtc,
      details.detectedTotalTtc,
      details.expectedTotalTtc,
    ];
    for (let j = 0; j < fallbackCandidates.length; j++) {
      const amount = normalizeAmount(fallbackCandidates[j]);
      if (amount !== 0) return amount;
    }
  }

  return 0;
};

const statusIsIncluded = (status) => {
  const s = String(status || '').toLowerCase();
  return s === 'valid' || s === 'conforme' || s === 'valide' || s === 'warning';
};

const isFinancialType = (documentType) => {
  const t = String(documentType || '').toLowerCase();
  return t === 'invoice' || t === 'quote' || t === 'facture' || t === 'devis';
};

router.get('/suppliers', async (_req, res) => {
  try {
    const docs = await CuratedDocument.find({
      'extractedData.siret': { $exists: true, $ne: '', $ne: null },
    })
      .select('vendorId documentType extractedData validation')
      .sort({ createdAt: -1 })
      .lean();

    const bySiret = new Map();
    for (let i = 0; i < docs.length; i++) {
      const d = docs[i];
      const siret = String(d?.extractedData?.siret || '').trim();
      if (!siret) continue;

      if (!bySiret.has(siret)) {
        bySiret.set(siret, {
          siret,
          companyName: d?.extractedData?.company_name || d?.extractedData?.companyName || '',
          status: d?.validation?.status || 'UNKNOWN',
          finalScore: d?.validation?.finalScore ?? 0,
          anomalyCount: d?.validation?.anomalyCount ?? 0,
          docCount: 0,
          vendorIds: new Set(),
          documentTypes: new Set(),
          amountTotal: 0,
        });
      }

      const row = bySiret.get(siret);
      row.docCount += 1;
      if (d?.vendorId) row.vendorIds.add(d.vendorId);
      if (d?.documentType) row.documentTypes.add(d.documentType);

      if (statusIsIncluded(d?.validation?.status) && isFinancialType(d?.documentType)) {
        row.amountTotal += extractFinancialAmount(d);
      }
    }

    const rows = Array.from(bySiret.values())
      .map((r) => ({
        ...r,
        vendorIds: Array.from(r.vendorIds),
        documentTypes: Array.from(r.documentTypes),
      }))
      .sort((a, b) => (b.finalScore ?? 0) - (a.finalScore ?? 0));

    res.json(
      rows.map((r) => ({
        siret: r.siret,
        companyName: r.companyName || '',
        status: r.status || 'UNKNOWN',
        finalScore: r.finalScore ?? 0,
        anomalyCount: r.anomalyCount ?? 0,
        docCount: r.docCount ?? 0,
        vendorIds: r.vendorIds || [],
        documentTypes: r.documentTypes || [],
        amountTotal: Number(r.amountTotal || 0),
      }))
    );
  } catch (err) {
    res.status(500).json({
      message: 'Erreur chargement anomalies fournisseurs',
      details: String(err?.message || err),
    });
  }
});


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

