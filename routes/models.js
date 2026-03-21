// backend/routes/models.js

const express = require('express');
const fs = require('fs');
const path = require('path');
const router = express.Router();

// Ruta para obtener el estado de los modelos
router.get('/status', (req, res) => {
  const statusFilePath = path.join(__dirname, '../data/status.json'); // Ruta donde está tu archivo status.json
  
  // Lee el archivo status.json
  fs.readFile(statusFilePath, 'utf-8', (err, data) => {
    if (err) {
      return res.status(500).json({ message: 'Error al leer el archivo de estado' });
    }
    res.json(JSON.parse(data)); // Devuelve el contenido del archivo JSON
  });
});

module.exports = router;
