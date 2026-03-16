const mongoose = require('mongoose');
// Importation de dotenv pour lire le fichier .env
require('dotenv').config(); 

const connectDB = async () => {
  try {
    // Tentative de connexion en utilisant l'URI caché dans le fichier .env
    const conn = await mongoose.connect(process.env.MONGO_URI);
    
    // Si ça fonctionne, on affiche un message de confirmation dans le terminal
    console.log(`MongoDB Connecté avec succès : ${conn.connection.host}`);
  } catch (error) {
    // Si la connexion échoue (mauvais mot de passe, serveur éteint)
    console.error(`Erreur critique de connexion MongoDB : ${error.message}`);
    // On arrête immédiatement le processus Node.js avec un code d'erreur (1)
    process.exit(1);
  }
};

// On exporte la fonction pour pouvoir l'appeler depuis le fichier principal du serveur
module.exports = connectDB;

//connectDB();