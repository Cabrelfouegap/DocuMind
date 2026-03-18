require('dotenv').config();

const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const path = require('path');

const documentRoutes = require('./routes/documents');
const validationRoutes = require('./routes/validation');

const app = express();
const listeningPort = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

app.use('/api/documents', documentRoutes);
app.use('/api/validation', validationRoutes);

mongoose
  .connect(process.env.MONGO_URI)
  .then(() => {
    app.listen(listeningPort, () => {});
  })
  .catch(() => {
    process.exit(1);
  });
