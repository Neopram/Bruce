// backend/routes/infer.js

const express = require('express');
const fs = require('fs');
const path = require('path');
const router = express.Router();

// Ruta para realizar la inferencia
router.post('/infer', (req, res) => {
  const { model, language, prompt } = req.body;  // Extrae los datos del body
  
  // Simula el proceso de inferencia (esto se puede reemplazar con lógica real de inferencia)
  const response = {
    output: `El modelo ${model} respondió en ${language} con el siguiente prompt: "${prompt}"`
  };

  const inferFilePath = path.join(__dirname, '../data/infer.json'); // Ruta donde se guardará el archivo infer.json
  
  // Guarda la respuesta en infer.json
  fs.writeFile(inferFilePath, JSON.stringify(response), (err) => {
    if (err) {
      return res.status(500).json({ message: 'Error al escribir en el archivo infer.json' });
    }
    res.json(response);  // Devuelve la respuesta generada
  });
});

module.exports = router;
