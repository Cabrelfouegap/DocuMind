const { GridFsStorage } = require('multer-gridfs-storage');
const multer = require('multer');
require('dotenv').config();

// Configuration du Data Lake (Zone Raw Physique)
const storage = new GridFsStorage({
  url: process.env.MONGO_URI,
  options: { useUnifiedTopology: true },
  file: (req, file) => {
    // Cette fonction définit comment le fichier physique est stocké
    return {
      bucketName: 'datalake_raw', // C'est l'équivalent de votre Bucket S3/MinIO
      filename: `${Date.now()}-${file.originalname}`
    };
  }
});

// Initialisation du middleware d'upload
const uploadToDataLake = multer({ storage });

module.exports = uploadToDataLake;