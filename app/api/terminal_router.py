from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer, TextGenerationPipeline
import torch
import logging
import time
from typing import Dict
from app.config.settings import config

router = APIRouter()

# Configuración de modelos soportados
MODEL_CONFIG = {
    "tinyllama": {
        "path": "./models/tinyllama",
        "max_tokens": 256,
        "temperature": 0.7,
        "top_p": 0.9
    },
    "phi3": {
        "path": "./models/phi3",
        "max_tokens": 512,
        "temperature": 0.6,
        "top_p": 0.85
    },
    "deepseek": {
        "path": "./models/deepseek",
        "max_tokens": 512,
        "temperature": 0.65,
        "top_p": 0.95
    }
}

# Caché de modelos cargados
model_cache: Dict[str, TextGenerationPipeline] = {}

# Logging
logger = logging.getLogger("Bruce.Terminal")
logger.setLevel(logging.INFO)

# Request Models
class TerminalQuery(BaseModel):
    prompt: str
    model: str = "tinyllama"
    max_tokens: int = None
    temperature: float = None
    top_p: float = None

class TerminalMessage(BaseModel):
    message: str

# === Función para cargar modelos dinámicamente ===
def load_model(model_key: str) -> TextGenerationPipeline:
    if model_key in model_cache:
        return model_cache[model_key]

    config_model = MODEL_CONFIG.get(model_key)
    if not config_model:
        raise ValueError(f"Modelo no soportado: {model_key}")

    logger.info(f"🔁 Cargando modelo '{model_key}' desde {config_model['path']}...")

    tokenizer = AutoTokenizer.from_pretrained(config_model["path"])
    model = AutoModelForCausalLM.from_pretrained(
        config_model["path"],
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
    )

    pipe = TextGenerationPipeline(
        model=model,
        tokenizer=tokenizer,
        device=0 if torch.cuda.is_available() else -1
    )

    model_cache[model_key] = pipe
    return pipe

# === Endpoint para frontend: POST /api/terminal/message ===
@router.post("/terminal/message")
async def terminal_message(payload: TerminalMessage):
    """
    Manejador para solicitudes desde Bruce Terminal UI.
    """
    try:
        prompt = payload.message.strip()
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt vacío")

        model_key = config.TERMINAL_DEFAULT_MODEL or "deepseek"
        model_config = MODEL_CONFIG[model_key]
        pipe = load_model(model_key)

        result = pipe(
            prompt,
            max_new_tokens=model_config["max_tokens"],
            do_sample=True,
            temperature=model_config["temperature"],
            top_p=model_config["top_p"]
        )

        return {"response": result[0]["generated_text"]}

    except Exception as e:
        logger.error(f"❌ Error en terminal/message: {str(e)}")
        raise HTTPException(status_code=500, detail="Error procesando el mensaje")

# === Endpoint para pruebas: GET /api/terminal/status ===
@router.get("/terminal/status")
async def terminal_status():
    return {
        "status": "Bruce terminal online",
        "default_model": config.TERMINAL_DEFAULT_MODEL,
        "available_models": list(MODEL_CONFIG.keys()),
        "device": "cuda" if torch.cuda.is_available() else "cpu"
    }

# === Endpoint alternativo: POST /terminal/ask (para pruebas avanzadas) ===
@router.post("/terminal/ask")
async def ask_terminal(query: TerminalQuery):
    start_time = time.time()
    try:
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
        logger.error(f"❌ Error generando respuesta: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al procesar el prompt")
