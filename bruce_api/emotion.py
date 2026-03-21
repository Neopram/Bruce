# Emotional processing and affective state management

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from bruce_api.utils import success_response, error_response, utc_now

router = APIRouter()

# ─── In-memory emotion state tracking ────────────────────────────────

_emotion_states: Dict[str, Dict[str, Any]] = {}
_emotion_history: Dict[str, List[Dict[str, Any]]] = {}

# Lazy-initialized analyzer instance
_analyzer = None


def _get_analyzer():
    """Lazy-load the EmotionalAnalyzer to avoid import issues at module level."""
    global _analyzer
    if _analyzer is None:
        try:
            from ai_core.emotion_engine import EmotionalAnalyzer
            _analyzer = EmotionalAnalyzer()
        except ImportError:
            _analyzer = _FallbackAnalyzer()
    return _analyzer


class _FallbackAnalyzer:
    """Fallback when the real EmotionalAnalyzer is not available."""
    import hashlib
    import random

    EMOTIONS = [
        "joy", "curiosity", "neutral", "fear", "anger", "sadness",
        "hope", "trust", "disgust", "surprise", "anticipation", "shame",
    ]

    async def analyze(self, text: str) -> dict:
        import hashlib, random as _rand
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16)
        rng = _rand.Random(seed)
        raw = {e: rng.uniform(0, 1) for e in self.EMOTIONS}
        total = sum(raw.values())
        dist = {k: round(v / total, 4) for k, v in raw.items()}
        primary = max(dist, key=dist.get)
        return {"primary": primary, "score": round(dist[primary], 2), "distribution": dist}


# ─── Pydantic Models ────────────────────────────────────────────────

class EmotionAnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to analyze for emotional content")
    user_id: Optional[str] = Field(None, description="User ID to track emotional state over time")


class EmotionAnalyzeResponse(BaseModel):
    primary_emotion: str
    score: float
    distribution: Dict[str, float]
    user_id: Optional[str]
    timestamp: str


class EmotionStateResponse(BaseModel):
    user_id: str
    current_emotion: str
    intensity: float
    last_updated: str
    analysis_count: int


class EmotionTrendEntry(BaseModel):
    emotion: str
    score: float
    timestamp: str


# ─── Endpoints ───────────────────────────────────────────────────────

@router.post("/analyze", response_model=EmotionAnalyzeResponse)
async def analyze_emotion(request: EmotionAnalyzeRequest):
    """
    Analyze the emotional tone of the provided text.
    Optionally tracks state over time if user_id is provided.
    """
    analyzer = _get_analyzer()
    result = await analyzer.analyze(request.text)

    now = utc_now()

    # Track per-user state if user_id provided
    if request.user_id:
        _emotion_states[request.user_id] = {
            "current_emotion": result["primary"],
            "intensity": result["score"],
            "last_updated": now,
            "analysis_count": _emotion_states.get(request.user_id, {}).get("analysis_count", 0) + 1,
        }

        user_history = _emotion_history.setdefault(request.user_id, [])
        user_history.append({
            "emotion": result["primary"],
            "score": result["score"],
            "timestamp": now,
        })
        # Keep last 100 entries per user
        if len(user_history) > 100:
            _emotion_history[request.user_id] = user_history[-100:]

    return EmotionAnalyzeResponse(
        primary_emotion=result["primary"],
        score=result["score"],
        distribution=result["distribution"],
        user_id=request.user_id,
        timestamp=now,
    )


@router.get("/state/{user_id}", response_model=EmotionStateResponse)
async def get_emotion_state(user_id: str):
    """Get the current emotional state for a user."""
    if user_id not in _emotion_states:
        raise HTTPException(
            status_code=404,
            detail=f"No emotional state found for user '{user_id}'. Analyze some text first.",
        )

    state = _emotion_states[user_id]
    return EmotionStateResponse(
        user_id=user_id,
        current_emotion=state["current_emotion"],
        intensity=state["intensity"],
        last_updated=state["last_updated"],
        analysis_count=state["analysis_count"],
    )


@router.get("/trend/{user_id}")
async def get_emotion_trend(user_id: str, limit: int = 20):
    """Get the emotional trend over time for a user."""
    if user_id not in _emotion_history:
        raise HTTPException(
            status_code=404,
            detail=f"No emotion history found for user '{user_id}'.",
        )

    history = _emotion_history[user_id][-limit:]

    # Compute dominant emotions summary
    emotion_counts: Dict[str, int] = {}
    for entry in history:
        emotion_counts[entry["emotion"]] = emotion_counts.get(entry["emotion"], 0) + 1

    dominant = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "unknown"

    return success_response(
        data={
            "user_id": user_id,
            "trend": history,
            "dominant_emotion": dominant,
            "emotion_frequency": emotion_counts,
            "total_analyses": len(_emotion_history.get(user_id, [])),
        },
        message=f"Emotion trend retrieved for user '{user_id}'.",
    )


@router.get("/influence")
async def get_emotion_influence():
    """
    Get a summary of how emotions are influencing the system across all users.
    Useful for understanding global emotional state patterns.
    """
    total_users = len(_emotion_states)
    if total_users == 0:
        return success_response(
            data={
                "total_tracked_users": 0,
                "global_emotion_distribution": {},
                "average_intensity": 0.0,
                "message": "No emotional data tracked yet.",
            },
        )

    # Aggregate current emotions across all users
    emotion_counts: Dict[str, int] = {}
    total_intensity = 0.0

    for state in _emotion_states.values():
        em = state["current_emotion"]
        emotion_counts[em] = emotion_counts.get(em, 0) + 1
        total_intensity += state["intensity"]

    return success_response(
        data={
            "total_tracked_users": total_users,
            "global_emotion_distribution": emotion_counts,
            "average_intensity": round(total_intensity / total_users, 4),
            "dominant_global_emotion": max(emotion_counts, key=emotion_counts.get),
        },
        message="Global emotional influence summary.",
    )
