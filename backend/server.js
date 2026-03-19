require('dotenv').config();

const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const path = require('path');

const documentRoutes = require('./routes/documents');
const conformityRoutes = require('./routes/conformity');

const app = express();
const listeningPort = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

app.use('/api/documents', documentRoutes);
app.use('/api/conformity', conformityRoutes);

mongoose
  .connect(process.env.MONGO_URI)
  .then(() => {
    app.listen(listeningPort, () => {
    });
  })
  .catch((error) => {
    process.exit(1);
  });
