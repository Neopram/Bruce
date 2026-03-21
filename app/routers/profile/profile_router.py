from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from app.core.auth_utils import get_current_user

router = APIRouter(prefix="/profile", tags=["profile"])

# ─── In-memory profile store ─────────────────────────────────────────

_profiles: Dict[str, Dict[str, Any]] = {}

# Default personality profiles
PERSONALITY_PRESETS = {
    "balanced": {
        "mode": "balanced",
        "tone": "neutral",
        "style": "precise",
        "bias": "none",
        "creativity": 0.5,
        "emotion": "stable",
    },
    "aggressive": {
        "mode": "aggressive",
        "tone": "confident",
        "style": "direct",
        "bias": "risk-seeking",
        "creativity": 0.7,
        "emotion": "driven",
    },
    "conservative": {
        "mode": "conservative",
        "tone": "cautious",
        "style": "detailed",
        "bias": "risk-averse",
        "creativity": 0.3,
        "emotion": "calm",
    },
    "creative": {
        "mode": "creative",
        "tone": "exploratory",
        "style": "narrative",
        "bias": "none",
        "creativity": 0.9,
        "emotion": "curious",
    },
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_or_create_profile(user_id: str) -> Dict[str, Any]:
    """Get existing profile or create a default one."""
    if user_id not in _profiles:
        _profiles[user_id] = {
            "user_id": user_id,
            "display_name": user_id,
            "personality": dict(PERSONALITY_PRESETS["balanced"]),
            "preferences": {
                "lang": "en",
                "theme": "dark",
                "notifications": True,
            },
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
        }
    return _profiles[user_id]


# ─── Pydantic Models ────────────────────────────────────────────────

class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    preferences: Optional[Dict[str, Any]] = None


class PersonalityUpdateRequest(BaseModel):
    mode: Optional[str] = None
    tone: Optional[str] = None
    style: Optional[str] = None
    bias: Optional[str] = None
    creativity: Optional[float] = Field(None, ge=0.0, le=1.0)
    emotion: Optional[str] = None


# ─── Endpoints ───────────────────────────────────────────────────────

@router.get("/")
async def get_profile(user: dict = Depends(get_current_user)):
    """Get the current user's profile."""
    user_id = user.get("sub", "anonymous")
    profile = _get_or_create_profile(user_id)
    return {"success": True, "data": profile}


@router.put("/")
async def update_profile(request: ProfileUpdateRequest, user: dict = Depends(get_current_user)):
    """Update the current user's profile."""
    user_id = user.get("sub", "anonymous")
    profile = _get_or_create_profile(user_id)

    if request.display_name is not None:
        profile["display_name"] = request.display_name

    if request.preferences is not None:
        profile["preferences"].update(request.preferences)

    profile["updated_at"] = _utc_now()

    return {"success": True, "data": profile, "message": "Profile updated."}


@router.get("/personality")
async def get_personality(user: dict = Depends(get_current_user)):
    """Get the current personality configuration."""
    user_id = user.get("sub", "anonymous")
    profile = _get_or_create_profile(user_id)

    # Also try to load from PersonalityEngine
    engine_personality = None
    try:
        from ai_core.personality_engine import PersonalityEngine
        engine = PersonalityEngine()
        engine_personality = engine.load_profile()
    except Exception:
        pass

    return {
        "user_personality": profile["personality"],
        "engine_personality": engine_personality,
        "available_presets": list(PERSONALITY_PRESETS.keys()),
    }


@router.put("/personality/{name}")
async def set_personality(name: str, user: dict = Depends(get_current_user)):
    """
    Set the personality to a preset by name, or apply custom values.
    If name matches a preset, use it. Otherwise treat it as a custom mode name.
    """
    user_id = user.get("sub", "anonymous")
    profile = _get_or_create_profile(user_id)

    if name in PERSONALITY_PRESETS:
        profile["personality"] = dict(PERSONALITY_PRESETS[name])
        profile["updated_at"] = _utc_now()

        # Also update PersonalityEngine if available
        try:
            from ai_core.personality_engine import PersonalityEngine
            engine = PersonalityEngine()
            engine.update_profile(**PERSONALITY_PRESETS[name])
        except Exception:
            pass

        return {
            "success": True,
            "personality": profile["personality"],
            "preset_applied": name,
            "message": f"Personality set to '{name}' preset.",
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Preset '{name}' not found. Available: {list(PERSONALITY_PRESETS.keys())}",
        )
