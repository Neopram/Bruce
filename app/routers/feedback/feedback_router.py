from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from app.core.auth_utils import get_current_user

router = APIRouter(prefix="/feedback", tags=["feedback"])

# ─── In-memory feedback store ────────────────────────────────────────

_feedback: List[Dict[str, Any]] = []
_ratings: List[Dict[str, Any]] = []


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Pydantic Models ────────────────────────────────────────────────

class FeedbackSubmitRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Original user prompt")
    response: str = Field(..., min_length=1, description="Bruce's response")
    quality: str = Field("neutral", description="Quality: positive, neutral, negative")
    model: str = Field("unknown", description="Model used")
    notes: str = Field("", description="Additional notes")


class FeedbackRateRequest(BaseModel):
    interaction_id: Optional[int] = Field(None, description="ID of the interaction to rate")
    score: float = Field(..., ge=0.0, le=10.0, description="Rating 0-10")
    aspect: str = Field("overall", description="What aspect is being rated")
    comment: str = Field("", description="Optional comment")


# ─── Endpoints ───────────────────────────────────────────────────────

@router.get("/")
async def feedback_root(user: dict = Depends(get_current_user)):
    return {"msg": f"Feedback module ready for user {user.get('sub', 'unknown')}."}


@router.post("/submit")
async def submit_feedback(request: FeedbackSubmitRequest, user: dict = Depends(get_current_user)):
    """Submit qualitative feedback on a prompt-response pair."""
    user_id = user.get("sub", "anonymous")

    entry = {
        "id": len(_feedback) + 1,
        "user_id": user_id,
        "prompt": request.prompt,
        "response": request.response,
        "quality": request.quality,
        "model": request.model,
        "notes": request.notes,
        "timestamp": _utc_now(),
    }
    _feedback.append(entry)

    # Persist via FeedbackCollector if available
    try:
        from ai_core.feedback_collector import FeedbackCollector
        collector = FeedbackCollector()
        collector.save_feedback(
            user_prompt=request.prompt,
            bruce_reply=request.response,
            quality=request.quality,
            model=request.model,
            notes=request.notes,
        )
    except Exception:
        pass

    return {"success": True, "data": entry, "message": "Feedback submitted."}


@router.post("/rate")
async def rate_interaction(request: FeedbackRateRequest, user: dict = Depends(get_current_user)):
    """Submit a numeric rating for an interaction or aspect."""
    user_id = user.get("sub", "anonymous")

    rating = {
        "id": len(_ratings) + 1,
        "user_id": user_id,
        "interaction_id": request.interaction_id,
        "score": request.score,
        "aspect": request.aspect,
        "comment": request.comment,
        "timestamp": _utc_now(),
    }
    _ratings.append(rating)

    return {"success": True, "data": rating, "message": "Rating recorded."}


@router.get("/summary")
async def feedback_summary(user: dict = Depends(get_current_user)):
    """Get a summary of all feedback collected."""
    total = len(_feedback)
    quality_counts = {"positive": 0, "neutral": 0, "negative": 0}
    model_counts: Dict[str, int] = {}

    for entry in _feedback:
        q = entry.get("quality", "neutral")
        if q in quality_counts:
            quality_counts[q] += 1
        m = entry.get("model", "unknown")
        model_counts[m] = model_counts.get(m, 0) + 1

    avg_rating = 0.0
    if _ratings:
        avg_rating = round(sum(r["score"] for r in _ratings) / len(_ratings), 2)

    return {
        "total_feedback": total,
        "total_ratings": len(_ratings),
        "average_rating": avg_rating,
        "by_quality": quality_counts,
        "by_model": model_counts,
    }


@router.get("/improvements")
async def get_improvements(user: dict = Depends(get_current_user)):
    """Analyze feedback and suggest areas for improvement."""
    if not _feedback:
        return {
            "suggestions": [],
            "message": "No feedback data available yet.",
        }

    negative = [e for e in _feedback if e.get("quality") == "negative"]

    # Group negative feedback by model
    neg_by_model: Dict[str, int] = {}
    for entry in negative:
        m = entry.get("model", "unknown")
        neg_by_model[m] = neg_by_model.get(m, 0) + 1

    suggestions = []
    for model, count in sorted(neg_by_model.items(), key=lambda x: -x[1]):
        total_for_model = sum(1 for e in _feedback if e.get("model") == model)
        ratio = count / total_for_model if total_for_model else 0
        suggestions.append({
            "model": model,
            "negative_count": count,
            "total_for_model": total_for_model,
            "negative_ratio": round(ratio, 2),
            "recommendation": (
                f"High negative ratio ({ratio:.0%}). Review and retrain."
                if ratio > 0.3 else f"Acceptable feedback ratio ({ratio:.0%})."
            ),
        })

    # Low-rated aspects
    if _ratings:
        aspect_scores: Dict[str, List[float]] = {}
        for r in _ratings:
            aspect_scores.setdefault(r["aspect"], []).append(r["score"])

        for aspect, scores in aspect_scores.items():
            avg = sum(scores) / len(scores)
            if avg < 5.0:
                suggestions.append({
                    "aspect": aspect,
                    "average_score": round(avg, 2),
                    "recommendation": f"Aspect '{aspect}' has low average score ({avg:.1f}/10).",
                })

    return {
        "total_feedback": len(_feedback),
        "negative_count": len(negative),
        "suggestions": suggestions,
    }
