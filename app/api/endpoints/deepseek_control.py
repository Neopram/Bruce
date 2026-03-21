"""
DeepSeek Control API - Manage the DeepSeek model lifecycle:
load, unload, run inference, and inspect configuration.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/deepseek", tags=["DeepSeek"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class InferRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Input prompt")
    max_tokens: int = Field(256, ge=1, le=4096)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    top_p: float = Field(0.9, ge=0.0, le=1.0)


class InferResponse(BaseModel):
    request_id: str
    output: str
    tokens_used: int
    latency_ms: float


class ModelConfig(BaseModel):
    model_name: str = "deepseek-ast-rewriter"
    quantization: Optional[str] = None
    max_context: int = 8192
    device: str = "cuda:0"


# ---------------------------------------------------------------------------
# In-memory state
# ---------------------------------------------------------------------------

_state = {
    "loaded": False,
    "model_name": "deepseek-ast-rewriter",
    "status": "idle",
    "requests_served": 0,
    "loaded_at": None,
    "config": ModelConfig().model_dump(),
}

_request_counter = 0


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/status")
async def deepseek_status():
    """Return current DeepSeek model status."""
    return {
        "loaded": _state["loaded"],
        "model": _state["model_name"],
        "status": _state["status"],
        "requests_served": _state["requests_served"],
        "loaded_at": _state["loaded_at"],
    }


@router.post("/load")
async def load_model(config: Optional[ModelConfig] = None):
    """Load the DeepSeek model into memory."""
    if _state["loaded"]:
        raise HTTPException(status_code=409, detail="Model is already loaded")

    cfg = config or ModelConfig()
    _state["loaded"] = True
    _state["model_name"] = cfg.model_name
    _state["status"] = "ready"
    _state["loaded_at"] = datetime.now(timezone.utc).isoformat()
    _state["config"] = cfg.model_dump()

    return {"message": "Model loaded successfully", "config": _state["config"]}


@router.post("/unload")
async def unload_model():
    """Unload the DeepSeek model from memory."""
    if not _state["loaded"]:
        raise HTTPException(status_code=409, detail="No model is currently loaded")

    _state["loaded"] = False
    _state["status"] = "idle"
    _state["loaded_at"] = None
    return {"message": "Model unloaded successfully"}


@router.post("/infer", response_model=InferResponse)
async def run_inference(request: InferRequest):
    """Run inference on the loaded DeepSeek model."""
    if not _state["loaded"]:
        raise HTTPException(status_code=503, detail="Model is not loaded. Call /load first.")

    global _request_counter
    _request_counter += 1
    _state["requests_served"] += 1

    # Simulated inference
    import time, hashlib
    start = time.monotonic()
    prompt_hash = hashlib.md5(request.prompt.encode()).hexdigest()[:8]
    simulated_output = (
        f"[DeepSeek output for prompt '{request.prompt[:50]}...'] "
        f"Analysis complete. Confidence: 0.92"
    )
    latency = round((time.monotonic() - start) * 1000 + 15.0, 2)

    return InferResponse(
        request_id=f"req-{_request_counter:06d}-{prompt_hash}",
        output=simulated_output,
        tokens_used=min(len(request.prompt.split()) * 3, request.max_tokens),
        latency_ms=latency,
    )


@router.get("/config")
async def get_config():
    """Return the current model configuration."""
    return {
        "loaded": _state["loaded"],
        "config": _state["config"],
    }
