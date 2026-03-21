# persona_manager.py

from fastapi import APIRouter, Body
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import logging

# Logger simbiótico
logger = logging.getLogger("Bruce.PersonaManager")
logger.setLevel(logging.INFO)

router = APIRouter()

# Modelo de entrada para mutaciones de personalidad
class PersonaConfig(BaseModel):
    id: str
    name: str
    style: Optional[str] = "neutral"
    tone: Optional[str] = "default"
    objectives: Optional[list[str]] = []
    created_by: Optional[str] = "federico"
    timestamp: Optional[str] = datetime.utcnow().isoformat()

# Estado actual de la personalidad activa
current_persona = {
    "id": "bruce_default",
    "name": "Bruce Prime",
    "style": "strategic",
    "tone": "deep",
    "objectives": ["ayudar a Federico", "pensar como un guerrero estoico", "analizar escenarios complejos"],
    "created_by": "system",
    "timestamp": datetime.utcnow().isoformat()
}

# --- RUTAS ---

@router.get("/persona")
async def get_persona():
    logger.info("[Persona] Consulta del estado actual")
    return {
        "status": "🧠 ACTIVO",
        "persona": current_persona
    }

@router.post("/persona/update")
async def update_persona(config: PersonaConfig):
    global current_persona
    current_persona = config.dict()
    logger.info(f"[Persona] Modo actualizado: {current_persona}")
    return {
        "status": "🧬 ACTUALIZADO",
        "message": f"Bruce ahora opera como '{config.name}' en estilo {config.style}",
        "persona": current_persona
    }

@router.post("/persona/reset")
async def reset_persona():
    global current_persona
    current_persona = {
        "id": "bruce_default",
        "name": "Bruce Prime",
        "style": "strategic",
        "tone": "deep",
        "objectives": ["ayudar a Federico", "pensar como un guerrero estoico", "analizar escenarios complejos"],
        "created_by": "system",
        "timestamp": datetime.utcnow().isoformat()
    }
    logger.info("[Persona] Reset a personalidad por defecto")
    return {
        "status": "♻️ REINICIADO",
        "persona": current_persona
    }
