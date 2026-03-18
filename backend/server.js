require('dotenv').config();

const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const path = require('path');

const app = express();
const listeningPort = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

mongoose
  .connect(process.env.MONGO_URI)
  .then(() => {

    const uploadToDataLake = require('./middlewares/datalakeUpload')(mongoose.connection);

    require('./middlewares/uploadInstance').set(uploadToDataLake);

    const documentRoutes = require('./routes/documents');
    app.use('/api/documents', documentRoutes);

    app.listen(listeningPort, () => {
    });
  })
  .catch((error) => {
    console.error('Erreur MongoDB:', error.message);
    process.exit(1);
  });