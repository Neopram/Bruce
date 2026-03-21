from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from app.core.auth_utils import get_current_user

router = APIRouter(prefix="/narrador", tags=["narrador"])

# ─── Available narration styles ──────────────────────────────────────

NARRATION_STYLES = {
    "analytical": {
        "name": "Analytical",
        "description": "Data-driven, precise, quantitative narration",
        "tone": "formal",
    },
    "storyteller": {
        "name": "Storyteller",
        "description": "Narrative-driven, engaging market stories",
        "tone": "engaging",
    },
    "concise": {
        "name": "Concise",
        "description": "Brief, to-the-point market summaries",
        "tone": "neutral",
    },
    "contrarian": {
        "name": "Contrarian",
        "description": "Devil's advocate perspective on market movements",
        "tone": "provocative",
    },
    "educational": {
        "name": "Educational",
        "description": "Explains market concepts alongside narration",
        "tone": "instructive",
    },
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Pydantic Models ────────────────────────────────────────────────

class NarrateRequest(BaseModel):
    market_state: Dict[str, Any] = Field(..., description="Current market state data")
    style: str = Field("analytical", description="Narration style to use")
    lang: str = Field("en", description="Language code")


class SummaryRequest(BaseModel):
    data: Dict[str, Any] = Field(..., description="Market data to summarize")
    period: str = Field("daily", description="Time period: hourly, daily, weekly")
    style: str = Field("concise", description="Summary style")


# ─── Narration Logic ─────────────────────────────────────────────────

def _narrate_market(market_state: Dict[str, Any], style: str) -> str:
    """Generate a narration of the given market state."""
    price = market_state.get("price", "N/A")
    change = market_state.get("change_pct", 0)
    volume = market_state.get("volume", "N/A")
    asset = market_state.get("asset", "the market")
    trend = "bullish" if isinstance(change, (int, float)) and change > 0 else "bearish"

    if style == "storyteller":
        return (
            f"The tale of {asset} continues to unfold. "
            f"At a price of {price}, the market has moved {change}% - "
            f"a {trend} chapter with volume reaching {volume}. "
            f"Traders watch with anticipation as the next move takes shape."
        )
    elif style == "concise":
        return f"{asset}: {price} ({change}%), Vol: {volume}. Trend: {trend}."
    elif style == "contrarian":
        counter = "bearish" if trend == "bullish" else "bullish"
        return (
            f"While the crowd sees {trend} signals on {asset} at {price} ({change}%), "
            f"the contrarian view suggests potential {counter} reversal. "
            f"Volume at {volume} may not sustain the current direction."
        )
    elif style == "educational":
        return (
            f"{asset} is currently trading at {price}, a {change}% move. "
            f"This {'positive' if trend == 'bullish' else 'negative'} movement, "
            f"combined with volume of {volume}, indicates {trend} momentum. "
            f"Understanding volume alongside price helps confirm trend strength."
        )
    else:  # analytical (default)
        return (
            f"Market analysis for {asset}: Price = {price}, Change = {change}%, "
            f"Volume = {volume}. Current bias: {trend}. "
            f"Key metrics suggest {'continuation' if abs(change) > 1 else 'consolidation'}."
        )


def _summarize_market(data: Dict[str, Any], period: str, style: str) -> str:
    """Generate a summary of market data for the given period."""
    assets = data.get("assets", [])
    overall = data.get("overall_change", 0)
    highlights = data.get("highlights", [])

    summary_parts = [f"Market summary ({period}):"]

    if isinstance(overall, (int, float)):
        direction = "up" if overall > 0 else "down"
        summary_parts.append(f"Overall market moved {direction} by {abs(overall)}%.")

    if assets:
        summary_parts.append(f"Tracked {len(assets)} assets.")

    if highlights:
        summary_parts.append(f"Key highlights: {'; '.join(str(h) for h in highlights[:3])}.")

    return " ".join(summary_parts)


# ─── Endpoints ───────────────────────────────────────────────────────

@router.get("/")
def narrador_root(user: dict = Depends(get_current_user)):
    return {"message": "Narrador module active", "user": user.get("sub")}


@router.post("/narrate")
async def narrate_market(request: NarrateRequest, user: dict = Depends(get_current_user)):
    """Generate a narrative description of the current market state."""
    if request.style not in NARRATION_STYLES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown style '{request.style}'. Available: {list(NARRATION_STYLES.keys())}",
        )

    narration = _narrate_market(request.market_state, request.style)

    # Also try the core narrador module for enrichment
    try:
        from app.core.narrador import explicar_operacion
        if "operacion" in request.market_state:
            enrichment = explicar_operacion(request.market_state["operacion"])
            narration += f"\n\n{enrichment}"
    except Exception:
        pass

    return {
        "narration": narration,
        "style": request.style,
        "timestamp": _utc_now(),
        "lang": request.lang,
    }


@router.post("/summary")
async def market_summary(request: SummaryRequest, user: dict = Depends(get_current_user)):
    """Generate a market summary for a given time period."""
    summary = _summarize_market(request.data, request.period, request.style)

    return {
        "summary": summary,
        "period": request.period,
        "style": request.style,
        "timestamp": _utc_now(),
    }


@router.get("/styles")
async def get_available_styles():
    """List all available narration styles."""
    return {
        "styles": NARRATION_STYLES,
        "default": "analytical",
        "total": len(NARRATION_STYLES),
    }
