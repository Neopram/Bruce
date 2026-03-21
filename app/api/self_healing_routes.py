# 📂 app/api/self_healing_routes.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import json
from app.services.self_healing_ai import execute_self_diagnosis

router = APIRouter()

# 📁 Ruta del log cognitivo persistente
LOG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../../deeptradex/logs/self_healing_history.json')
)

# ✅ Modelo para petición manual desde frontend
class DiagnosisRequest(BaseModel):
    source: Optional[str] = "api"
    reason: Optional[str] = "Manual trigger from frontend"

# -------------------- POST /self-healing/diagnose -------------------- #
@router.post("/self-healing/diagnose", tags=["Self-Healing"])
def trigger_self_healing(req: DiagnosisRequest):
    """
    🧠 Ejecuta un diagnóstico cognitivo usando DeepSeek y guarda el resultado.
    """
    try:
        execute_self_diagnosis(source=req.source, reason=req.reason)
        return {"status": "🧠 Diagnosis triggered", "source": req.source, "reason": req.reason}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during diagnosis: {str(e)}")

# -------------------- GET /self-healing/history -------------------- #
@router.get("/self-healing/history", tags=["Self-Healing"])
def get_self_healing_history():
    """
    📜 Retorna el historial de diagnósticos previos guardados en JSON.
    """
    try:
        if not os.path.exists(LOG_PATH):
            return []

        with open(LOG_PATH, "r") as f:
            data = json.load(f)
        return {"history": data, "entries": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read history log: {str(e)}")
