# Reinforcement learning with human feedback (RLHF)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from bruce_api.utils import success_response, error_response, utc_now

router = APIRouter()

# ─── In-memory feedback store ────────────────────────────────────────

_feedback_entries: List[Dict[str, Any]] = []
_ratings: Dict[str, List[Dict[str, Any]]] = {}  # model_name -> ratings
_model_scores: Dict[str, Dict[str, Any]] = {}   # aggregated model scores

# Lazy-loaded collector
_collector = None


def _get_collector():
    global _collector
    if _collector is None:
        try:
            from ai_core.feedback_collector import FeedbackCollector
            _collector = FeedbackCollector()
        except Exception:
            _collector = None
    return _collector


# ─── Pydantic Models ────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    prompt: str = Field(..., min_length=1, description="Original prompt sent to Bruce")
    response: str = Field(..., min_length=1, description="Bruce's response")
    quality: str = Field("neutral", description="Quality label: positive, neutral, negative")
    model: str = Field("unknown", description="Model that generated the response")
    notes: str = Field("", description="Free-form notes about the interaction")


class RateRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1, description="Model being rated")
    score: float = Field(..., ge=0.0, le=10.0, description="Rating score (0-10)")
    context: str = Field("", description="What was being evaluated")


class FeedbackEntry(BaseModel):
    id: int
    user_id: str
    prompt: str
    response: str
    quality: str
    model: str
    notes: str
    timestamp: str


# ─── Endpoints ───────────────────────────────────────────────────────

@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Submit qualitative feedback for a prompt-response pair."""
    entry = {
        "id": len(_feedback_entries) + 1,
        "user_id": request.user_id,
        "prompt": request.prompt,
        "response": request.response,
        "quality": request.quality,
        "model": request.model,
        "notes": request.notes,
        "timestamp": utc_now(),
    }
    _feedback_entries.append(entry)

    # Also persist via FeedbackCollector if available
    collector = _get_collector()
    if collector:
        try:
            collector.save_feedback(
                user_prompt=request.prompt,
                bruce_reply=request.response,
                quality=request.quality,
                model=request.model,
                notes=request.notes,
            )
        except Exception:
            pass  # Non-critical persistence

    return success_response(
        data=entry,
        message="Feedback recorded successfully.",
    )


@router.post("/rate")
async def rate_model(request: RateRequest):
    """Submit a numeric rating for a specific model."""
    rating = {
        "user_id": request.user_id,
        "score": request.score,
        "context": request.context,
        "timestamp": utc_now(),
    }

    model_ratings = _ratings.setdefault(request.model, [])
    model_ratings.append(rating)

    # Update aggregated score
    scores = [r["score"] for r in model_ratings]
    _model_scores[request.model] = {
        "model": request.model,
        "average_score": round(sum(scores) / len(scores), 2),
        "total_ratings": len(scores),
        "min_score": min(scores),
        "max_score": max(scores),
    }

    return success_response(
        data=rating,
        message=f"Rating for model '{request.model}' recorded.",
    )


@router.get("/summary")
async def feedback_summary():
    """Get a summary of all feedback collected."""
    total = len(_feedback_entries)

    quality_counts = {"positive": 0, "neutral": 0, "negative": 0}
    model_counts: Dict[str, int] = {}

    for entry in _feedback_entries:
        q = entry["quality"]
        if q in quality_counts:
            quality_counts[q] += 1
        model_counts[entry["model"]] = model_counts.get(entry["model"], 0) + 1

    # Also try to get persistent stats
    collector = _get_collector()
    persistent_stats = None
    if collector:
        try:
            persistent_stats = collector.get_feedback_stats()
        except Exception:
            pass

    return success_response(
        data={
            "total_feedback": total,
            "by_quality": quality_counts,
            "by_model": model_counts,
            "persistent_stats": persistent_stats,
        },
        message="Feedback summary generated.",
    )


@router.get("/improvements")
async def get_improvements():
    """
    Analyze feedback to suggest improvements.
    Returns areas where negative feedback is concentrated.
    """
    if not _feedback_entries:
        return success_response(
            data={"suggestions": [], "message": "No feedback data available yet."},
        )

    # Find models and patterns with negative feedback
    negative_entries = [e for e in _feedback_entries if e["quality"] == "negative"]
    positive_entries = [e for e in _feedback_entries if e["quality"] == "positive"]

    negative_models: Dict[str, int] = {}
    for entry in negative_entries:
        negative_models[entry["model"]] = negative_models.get(entry["model"], 0) + 1

    suggestions = []

    for model, neg_count in sorted(negative_models.items(), key=lambda x: -x[1]):
        total_for_model = sum(1 for e in _feedback_entries if e["model"] == model)
        neg_ratio = neg_count / total_for_model if total_for_model > 0 else 0
        if neg_ratio > 0.3:
            suggestions.append({
                "model": model,
                "negative_feedback_count": neg_count,
                "negative_ratio": round(neg_ratio, 2),
                "recommendation": f"Model '{model}' has a high negative feedback ratio ({neg_ratio:.0%}). Consider retraining or adjusting parameters.",
            })

    if not suggestions:
        suggestions.append({
            "model": "all",
            "recommendation": "Feedback is generally positive. Continue current approach.",
        })

    return success_response(
        data={
            "total_feedback": len(_feedback_entries),
            "negative_count": len(negative_entries),
            "positive_count": len(positive_entries),
            "suggestions": suggestions,
        },
        message="Improvement analysis complete.",
    )


@router.get("/model-ranking")
async def model_ranking():
    """Get models ranked by their average rating score."""
    if not _model_scores:
        return success_response(
            data={"ranking": [], "message": "No model ratings available yet."},
        )

    ranking = sorted(
        _model_scores.values(),
        key=lambda x: x["average_score"],
        reverse=True,
    )

    for i, entry in enumerate(ranking):
        entry["rank"] = i + 1

    return success_response(
        data={"ranking": ranking},
        message="Model ranking generated.",
    )
