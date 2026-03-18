const multer = require('multer');
const { GridFSBucket } = require('mongodb');
const { Readable } = require('stream');

module.exports = (connection) => {
  return {
    array: (fieldName) => (req, res, next) => {
      multer({ storage: multer.memoryStorage() }).array(fieldName)(req, res, async (err) => {
        if (err) return next(err);
        if (!req.files || req.files.length === 0) return next();

        const bucket = new GridFSBucket(connection.db, { bucketName: 'datalake_raw' });
        const uploaded = [];

        for (const file of req.files) {
          await new Promise((resolve, reject) => {
            const filename = `${Date.now()}-${file.originalname}`;
            const stream = bucket.openUploadStream(filename, { contentType: file.mimetype });
            Readable.from(file.buffer).pipe(stream);
            stream.on('finish', () => {
              uploaded.push({
                filename: stream.filename,
                originalname: file.originalname,
                mimetype: file.mimetype
              });
              resolve();
            });
            stream.on('error', reject);
          });
        }

        req.files = uploaded;
        next();
      });
    }
  };
};