"""
Cognitive Routes - Status, inference, memory, self-reflection,
and personality management for the cognitive subsystem.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/cognitive", tags=["Cognitive"])

DIGEST_PATH = os.path.abspath("deeptradex/logs/cognitive_digest.json")


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class InferRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    context: dict = Field(default_factory=dict)
    max_tokens: int = Field(512, ge=1, le=4096)


class MemoryEntry(BaseModel):
    content: str
    category: str = "general"
    importance: float = Field(0.5, ge=0.0, le=1.0)


class PersonalityProfile(BaseModel):
    name: str
    traits: dict = Field(default_factory=dict)
    tone: str = "neutral"
    risk_appetite: str = "moderate"
    verbosity: str = "medium"


# ---------------------------------------------------------------------------
# In-memory state
# ---------------------------------------------------------------------------

_personalities: Dict[str, dict] = {
    "default": {
        "name": "default",
        "traits": {"analytical": 0.8, "cautious": 0.6, "creative": 0.5},
        "tone": "neutral",
        "risk_appetite": "moderate",
        "verbosity": "medium",
    },
    "aggressive": {
        "name": "aggressive",
        "traits": {"analytical": 0.7, "cautious": 0.2, "creative": 0.6},
        "tone": "confident",
        "risk_appetite": "high",
        "verbosity": "concise",
    },
    "conservative": {
        "name": "conservative",
        "traits": {"analytical": 0.9, "cautious": 0.9, "creative": 0.3},
        "tone": "formal",
        "risk_appetite": "low",
        "verbosity": "detailed",
    },
}

_active_personality: str = "default"

_user_memories: Dict[str, List[dict]] = {}

_reflections: List[dict] = []

_inference_count: int = 0


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/status")
async def cognitive_status():
    """Return current cognitive system status."""
    return {
        "status": "operational",
        "active_personality": _active_personality,
        "personality_profile": _personalities.get(_active_personality),
        "total_inferences": _inference_count,
        "memory_users": len(_user_memories),
        "reflections_count": len(_reflections),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/infer")
async def cognitive_infer(request: InferRequest):
    """Run a cognitive inference with the active personality."""
    global _inference_count
    _inference_count += 1

    personality = _personalities.get(_active_personality, _personalities["default"])

    # Simulated inference
    response_text = (
        f"[Cognitive inference #{_inference_count}] "
        f"Personality: {personality['name']} | Tone: {personality['tone']} | "
        f"Analysis of '{request.prompt[:80]}' complete."
    )

    return {
        "request_id": f"cog-{_inference_count:06d}",
        "response": response_text,
        "personality_used": personality["name"],
        "tokens_used": min(len(request.prompt.split()) * 4, request.max_tokens),
        "context_keys": list(request.context.keys()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/memory/{user_id}")
async def get_user_memory(user_id: str):
    """Get stored memory entries for a specific user."""
    memories = _user_memories.get(user_id, [])
    return {
        "user_id": user_id,
        "entry_count": len(memories),
        "memories": memories,
    }


@router.post("/memory/{user_id}")
async def store_user_memory(user_id: str, entry: MemoryEntry):
    """Store a new memory entry for a user."""
    record = {
        "id": str(uuid.uuid4()),
        "content": entry.content,
        "category": entry.category,
        "importance": entry.importance,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if user_id not in _user_memories:
        _user_memories[user_id] = []
    _user_memories[user_id].append(record)

    return {"status": "stored", "entry": record}


@router.post("/reflect")
async def trigger_reflection():
    """Trigger a self-reflection cycle and return insights."""
    personality = _personalities.get(_active_personality, _personalities["default"])

    reflection = {
        "id": str(uuid.uuid4()),
        "personality": personality["name"],
        "total_inferences": _inference_count,
        "memory_coverage": {uid: len(mems) for uid, mems in _user_memories.items()},
        "insights": [
            f"Processed {_inference_count} inferences under '{personality['name']}' personality.",
            f"Tracking memories for {len(_user_memories)} user(s).",
            f"Risk appetite is set to '{personality['risk_appetite']}' - consider adjusting if market conditions shift.",
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    _reflections.append(reflection)
    return reflection


@router.get("/personality")
async def get_personality():
    """Return the current active personality and all available profiles."""
    return {
        "active": _active_personality,
        "profile": _personalities.get(_active_personality),
        "available": list(_personalities.keys()),
    }


@router.put("/personality/{name}")
async def switch_personality(name: str):
    """Switch the active cognitive personality."""
    global _active_personality

    if name not in _personalities:
        raise HTTPException(
            status_code=404,
            detail=f"Personality '{name}' not found. Available: {list(_personalities.keys())}",
        )

    _active_personality = name
    return {
        "status": "switched",
        "active_personality": name,
        "profile": _personalities[name],
    }


@router.post("/personality")
async def create_personality(profile: PersonalityProfile):
    """Create or update a personality profile."""
    _personalities[profile.name] = profile.model_dump()
    return {"status": "saved", "profile": _personalities[profile.name]}


@router.get("/digest")
async def get_cognitive_digest():
    """Return the structured cognitive memory generated by the Reinforcer."""
    try:
        if not os.path.exists(DIGEST_PATH):
            return {"timeline": [], "tags": {}, "insights": ["No cognitive digest found."]}
        with open(DIGEST_PATH, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read cognitive digest: {str(e)}")
