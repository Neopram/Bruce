from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import logging
import json
import os
from datetime import datetime
from deeptradex.tia_agent import TIAAgent

router = APIRouter()
LOG_FILE = os.path.abspath("deeptradex/logs/tia_agent_output.json")

class TIARequest(BaseModel):
    command: str
    context: Dict[str, Any] = {}

def log_tia_execution(command: str, context: dict, output: str):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "command": command,
        "context": context,
        "output": output
    }

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                history = json.load(f)
        else:
            history = []

        history.append(log_entry)

        with open(LOG_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        logging.warning(f"❗ Error logging TIA output: {e}")

@router.post("/tia-agent/execute", tags=["TIAAgent"])
def execute_tia_command(payload: TIARequest):
    """
    🧠 Ejecuta un comando cognitivo a través del agente TIA con contexto.
    """
    try:
        agent = TIAAgent()
        result = agent.execute(payload.command, payload.context)
        log_tia_execution(payload.command, payload.context, result)
        return {"result": result}
    except Exception as e:
        logging.error(f"TIAAgent error: {e}")
        raise HTTPException(status_code=500, detail="TIA execution failed")

@router.get("/tia-agent/history", tags=["TIAAgent"])
def get_tia_history():
    """
    📜 Devuelve el historial de ejecuciones del TIAAgent.
    """
    try:
        if not os.path.exists(LOG_FILE):
            return []
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error reading TIA history: {e}")
        raise HTTPException(status_code=500, detail="Failed to read history")
