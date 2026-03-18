const express = require('express');
const router = express.Router();

const CuratedDocument = require('../models/CuratedDocument');

router.get('/results', async (req, res) => {
  try {
    const results = await CuratedDocument.aggregate([
      {
        $sort: {
          'validation.lastCheckedAt': -1,
          createdAt: -1,
        },
      },
      {
        $group: {
          _id: '$vendorId',
          validation: { $first: '$validation' },
        },
      },
      {
        $project: {
          _id: 0,
          vendorId: '$_id',
          validation: 1,
        },
      },
      {
        $sort: { vendorId: 1 },
      },
    ]);

    res.json(results);
  } catch (err) {
    console.error('Erreur récupération validation results:', err);
    res.status(500).json({ message: 'Erreur serveur (validation results)' });
  }
});

module.exports = router;

