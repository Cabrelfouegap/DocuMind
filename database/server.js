const express = require('express');
const cors = require('cors');
const connectDB = require('./config/db');
require('dotenv').config();

// 1. Initialisation de l'application Express
const app = express();

// 2. Appel de fonction de connexion à la base de données
connectDB();

// 3. Configuration des Middlewares (Sécurité et format de données)
app.use(cors()); // Autorise le Front-end à communiquer avec cette API
app.use(express.json()); // Permet à l'API de comprendre les données envoyées en format JSON

// 4. Création d'une route de test pour vérifier que l'API répond
app.get('/api/status', (req, res) => {
  res.status(200).json({ 
    status: 'success',
    message: 'API DocuMind opérationnelle',
    database: 'MongoDB Connecté'
  });
});

// 5. Définition du port du serveur 
const PORT = process.env.PORT || 5000;

// 6. Lancement du serveur
app.listen(PORT, () => {
  console.log(`Serveur API démarré sur le port ${PORT}`);
});