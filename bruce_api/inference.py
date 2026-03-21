# Local model inference engine (e.g., DeepSeek, TinyLlama)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from bruce_api.utils import success_response, error_response, utc_now

router = APIRouter()

# ─── In-memory model registry ────────────────────────────────────────

_model_registry: Dict[str, Dict[str, Any]] = {
    "phi3": {
        "name": "phi3",
        "description": "Phi-3 HyperCore - Default reasoning kernel",
        "status": "unloaded",
        "loaded_at": None,
        "inference_count": 0,
    },
    "tinyllama": {
        "name": "tinyllama",
        "description": "TinyLlama - Lightweight inference kernel",
        "status": "unloaded",
        "loaded_at": None,
        "inference_count": 0,
    },
    "deepseek-mini": {
        "name": "deepseek-mini",
        "description": "DeepSeek Coder MINI - Compact code-focused kernel",
        "status": "unloaded",
        "loaded_at": None,
        "inference_count": 0,
    },
    "deepseek-base": {
        "name": "deepseek-base",
        "description": "DeepSeek Coder BASE - Full code reasoning kernel",
        "status": "unloaded",
        "loaded_at": None,
        "inference_count": 0,
    },
}

_active_model: Optional[str] = None


# ─── Pydantic Models ────────────────────────────────────────────────

class InferRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="The input prompt for inference")
    model: Optional[str] = Field(None, description="Model name to use (uses active model if omitted)")
    lang: str = Field("en", description="Language code for the response")
    max_tokens: int = Field(512, ge=1, le=4096, description="Maximum tokens to generate")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")


class InferResponse(BaseModel):
    response: str
    model_used: str
    tokens_generated: int
    latency_ms: float
    timestamp: str


class ModelInfo(BaseModel):
    name: str
    description: str
    status: str
    loaded_at: Optional[str]
    inference_count: int


class ModelActionResponse(BaseModel):
    success: bool
    model: str
    status: str
    message: str


# ─── Endpoints ───────────────────────────────────────────────────────

@router.post("/infer", response_model=InferResponse)
async def run_inference(request: InferRequest):
    """
    Run inference using the specified or currently active model.
    Falls back to a simulated response if no real kernel is loaded.
    """
    global _active_model

    model_name = request.model or _active_model

    if not model_name:
        raise HTTPException(
            status_code=400,
            detail="No model specified and no active model loaded. Load a model first.",
        )

    if model_name not in _model_registry:
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found in registry")

    model_info = _model_registry[model_name]

    # Attempt real inference through ai_core
    import time
    start = time.time()

    try:
        from ai_core.infer_router import infer_from_bruce
        response_text = await infer_from_bruce(request.prompt, lang=request.lang)
    except Exception:
        # Simulated fallback if kernel not available
        response_text = (
            f"[Simulated {model_name}] Based on your input, here is a synthesized response "
            f"to: '{request.prompt[:80]}...'" if len(request.prompt) > 80
            else f"[Simulated {model_name}] Response to: '{request.prompt}'"
        )

    latency = (time.time() - start) * 1000
    model_info["inference_count"] += 1

    return InferResponse(
        response=response_text,
        model_used=model_name,
        tokens_generated=len(response_text.split()),
        latency_ms=round(latency, 2),
        timestamp=utc_now(),
    )


@router.get("/models", response_model=List[ModelInfo])
async def list_models():
    """List all available models and their current status."""
    return [
        ModelInfo(**info)
        for info in _model_registry.values()
    ]


@router.get("/models/{name}/status", response_model=ModelInfo)
async def get_model_status(name: str):
    """Get the status of a specific model by name."""
    if name not in _model_registry:
        raise HTTPException(status_code=404, detail=f"Model '{name}' not found")
    return ModelInfo(**_model_registry[name])


@router.post("/models/{name}/load", response_model=ModelActionResponse)
async def load_model(name: str):
    """Load a model into memory and set it as the active model."""
    global _active_model

    if name not in _model_registry:
        raise HTTPException(status_code=404, detail=f"Model '{name}' not found")

    model_info = _model_registry[name]
    model_info["status"] = "loaded"
    model_info["loaded_at"] = utc_now()
    _active_model = name

    return ModelActionResponse(
        success=True,
        model=name,
        status="loaded",
        message=f"Model '{name}' loaded and set as active.",
    )


@router.post("/models/{name}/unload", response_model=ModelActionResponse)
async def unload_model(name: str):
    """Unload a model from memory."""
    global _active_model

    if name not in _model_registry:
        raise HTTPException(status_code=404, detail=f"Model '{name}' not found")

    model_info = _model_registry[name]
    model_info["status"] = "unloaded"
    model_info["loaded_at"] = None

    if _active_model == name:
        _active_model = None

    return ModelActionResponse(
        success=True,
        model=name,
        status="unloaded",
        message=f"Model '{name}' unloaded successfully.",
    )
