# 📂 Ruta: C:\Users\feder\Desktop\OKK_Gorilla_Bot\app\api\routes\simulation_api.py

from fastapi import APIRouter, HTTPException
from typing import List, Dict
import os
import json
import logging

router = APIRouter()

# Ruta completa y segura del archivo de simulación
SIMULATION_PATH = os.path.join("data", "simulation", "last_episode.json")
os.makedirs(os.path.dirname(SIMULATION_PATH), exist_ok=True)

@router.get("/simulation/episode", response_model=List[Dict])
async def get_simulation_episode():
    """
    Devuelve el episodio de simulación más reciente.
    Utilizado por TradeSimulationPanel.tsx para reproducir acciones del agente RL.
    """
    try:
        if not os.path.exists(SIMULATION_PATH):
            raise HTTPException(status_code=404, detail=f"Archivo no encontrado en {SIMULATION_PATH}")

        with open(SIMULATION_PATH, "r") as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise HTTPException(status_code=500, detail="Formato de simulación inválido. Se esperaba una lista.")

            logging.info(f"✅ Episodio de simulación cargado: {len(data)} pasos.")
            return data

    except Exception as e:
        logging.error(f"❌ Error al cargar la simulación: {str(e)}")
        raise HTTPException(status_code=500, detail="Error cargando la simulación desde el backend.")