const mongoose = require('mongoose');
const { GridFSBucket } = require('mongodb');
const fs = require('fs');

const envoyerFichierDansGridFS = (cheminLocal, nomGridFS) => {
  return new Promise((resolve, reject) => {
    const db = mongoose.connection.db;
    const bucket = new GridFSBucket(db, { bucketName: 'datalake_raw' });

    const streamLecture = fs.createReadStream(cheminLocal);
    const streamEcriture = bucket.openUploadStream(nomGridFS);

    streamLecture.pipe(streamEcriture);

    streamEcriture.on('finish', () => {
      resolve(streamEcriture.id);
    });

    streamEcriture.on('error', (err) => {
      reject(err);
    });
  });
};

module.exports = { envoyerFichierDansGridFS };
