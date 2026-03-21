# terminal.py – Módulo de interacción con modelos LLM locales
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM, TextGenerationPipeline
import torch
import logging
import time
from typing import Dict
from app.config.settings import config

router = APIRouter()

# 📦 Configuración de modelos desde .env
MODEL_CONFIG = {
    "phi3": {
        "path": config.PHI3_MODEL_PATH,
        "max_tokens": 512,
        "temperature": 0.6,
        "top_p": 0.85
    },
    "deepseek": {
        "path": config.DEEPSEEK_MODEL_PATH,
        "max_tokens": 512,
        "temperature": 0.65,
        "top_p": 0.95
    },
    "tinyllama": {
        "path": config.TINYLLAMA_MODEL_PATH,
        "max_tokens": 256,
        "temperature": 0.7,
        "top_p": 0.9
    }
}

# 🔁 Cache de modelos
model_cache: Dict[str, TextGenerationPipeline] = {}

# 🛠️ Logger
logger = logging.getLogger("Bruce.Terminal")
logger.setLevel(logging.INFO)

# 📬 Esquemas de entrada
class TerminalQuery(BaseModel):
    prompt: str
    model: str = config.TERMINAL_DEFAULT_MODEL
    max_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None

class TerminalMessage(BaseModel):
    message: str

# 🔄 Carga de modelos
def load_model(model_key: str) -> TextGenerationPipeline:
    if model_key in model_cache:
        return model_cache[model_key]

    config_model = MODEL_CONFIG.get(model_key)
    if not config_model:
        raise ValueError(f"Modelo no soportado: {model_key}")

    logger.info(f"🔁 Cargando modelo '{model_key}' desde {config_model['path']}...")

    tokenizer = AutoTokenizer.from_pretrained(config_model["path"], local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        config_model["path"],
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        local_files_only=True
    )

    pipe = TextGenerationPipeline(
        model=model,
        tokenizer=tokenizer,
        device=0 if torch.cuda.is_available() else -1
    )

    model_cache[model_key] = pipe
    return pipe

# 🚀 POST /api/terminal/message – modo simple
@router.post("/message")
async def terminal_message(payload: TerminalMessage):
    try:
        prompt = payload.message.strip()
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt vacío")

        model_key = config.TERMINAL_DEFAULT_MODEL
        config_model = MODEL_CONFIG[model_key]
        pipe = load_model(model_key)

        result = pipe(
            prompt,
            max_new_tokens=config_model["max_tokens"],
            do_sample=True,
            temperature=config_model["temperature"],
            top_p=config_model["top_p"]
        )

        logger.info(f"✅ Prompt procesado con éxito. Respuesta parcial: {result[0].get('generated_text', '')[:50]}...")

        if not result or "generated_text" not in result[0]:
            raise HTTPException(status_code=500, detail="Modelo no generó respuesta válida.")

        return {"response": result[0]["generated_text"]}

    except Exception as e:
        logger.error(f"❌ Error en terminal/message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error procesando el mensaje: {str(e)}")

# 🔍 GET /api/terminal/status – Información del sistema
@router.get("/status")
async def terminal_status():
    return {
        "status": "Bruce terminal online",
        "default_model": config.TERMINAL_DEFAULT_MODEL,
        "available_models": list(MODEL_CONFIG.keys()),
        "device": "cuda" if torch.cuda.is_available() else "cpu"
    }

# 🧠 POST /api/terminal/ask – modo avanzado
@router.post("/ask")
async def ask_terminal(query: TerminalQuery):
    start_time = time.time()
    try:
        if query.model not in MODEL_CONFIG:
            raise HTTPException(status_code=400, detail=f"Modelo no disponible: {query.model}")

        pipe = load_model(query.model)
        config_model = MODEL_CONFIG[query.model]

        max_tokens = query.max_tokens or config_model["max_tokens"]
        temperature = query.temperature or config_model["temperature"]
        top_p = query.top_p or config_model["top_p"]

        result = pipe(
            query.prompt,
            max_new_tokens=max_tokens,
            do_sample=True,
            temperature=temperature,
            top_p=top_p
        )

        return {
            "model": query.model,
            "tokens_used": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "elapsed": round(time.time() - start_time, 2),
            "response": result[0]["generated_text"]
        }

    except Exception as e:
        logger.error(f"❌ Error generando respuesta avanzada: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al procesar el prompt")
