from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import logging
import os
import requests

# Compatibilidad con API estilo OpenAI si se usa remotamente
try:
    import openai
except ImportError:
    openai = None

router = APIRouter()

# === Configuración ===

USE_OLLAMA_LOCAL = os.getenv("USE_OLLAMA", "true").lower() == "true"
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-coder:7b-instruct")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")  # Para modo remoto
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-reasoner")

# === Input Schema ===

class DeepSeekCommand(BaseModel):
    command: str
    context: Dict[str, Any] = {}

# === Endpoint ===

@router.post("/ai/deepseek/control")
async def control_deepseek(cmd: DeepSeekCommand):
    prompt = f"""
    You are an autonomous cognitive trading supervisor.
    
    COMMAND: {cmd.command}
    CONTEXT: {cmd.context}
    
    Generate a plan of action, backend functions to trigger (if needed), and expected impact.
    """

    if USE_OLLAMA_LOCAL:
        # === MODO LOCAL (OLLAMA) ===
        try:
            payload = {
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": "You are DeepSeek, system controller."},
                    {"role": "user", "content": prompt}
                ]
            }
            response = requests.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            result = response.json()
            reply = result["message"]["content"].strip()
            logging.info(f"[DeepSeek Local] ✅ {reply}")
            return {"response": reply}
        except Exception as e:
            logging.error(f"❌ DeepSeek local error: {e}")
            raise HTTPException(status_code=500, detail="Error using local DeepSeek model.")

    else:
        # === MODO REMOTO (API tipo OpenAI) ===
        if not DEEPSEEK_API_KEY or not openai:
            raise HTTPException(status_code=500, detail="DeepSeek API not configured or OpenAI module missing.")
        try:
            openai.api_key = DEEPSEEK_API_KEY
            response = openai.ChatCompletion.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "You are the DeepSeek cognitive controller."},
                    {"role": "user", "content": prompt},
                ],
            )
            reply = response.choices[0].message.content.strip()
            logging.info(f"[DeepSeek API] ✅ {reply}")
            return {"response": reply}
        except Exception as e:
            logging.error(f"❌ DeepSeek remote error: {e}")
            raise HTTPException(status_code=500, detail="Error processing command with DeepSeek API.")
