from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import uuid
import random

from app.core.auth_utils import get_current_user

router = APIRouter(prefix="/arbitraje", tags=["arbitraje"])

# ─── In-memory stores ────────────────────────────────────────────────

_opportunities: List[Dict[str, Any]] = []
_trade_history: List[Dict[str, Any]] = []
_stats: Dict[str, Any] = {
    "total_scans": 0,
    "opportunities_found": 0,
    "trades_executed": 0,
    "successful_trades": 0,
    "total_profit": 0.0,
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Pydantic Models ────────────────────────────────────────────────

class ArbitrageExecuteRequest(BaseModel):
    opportunity_id: str = Field(..., description="ID of the opportunity to execute")
    amount: float = Field(..., gt=0, description="Amount to trade")
    confirm: bool = Field(False, description="Confirm execution (safety check)")


# ─── Opportunity Scanner ─────────────────────────────────────────────

def _scan_opportunities() -> List[Dict[str, Any]]:
    """
    Scan for arbitrage opportunities across exchanges.
    Returns simulated opportunities for demonstration.
    """
    _stats["total_scans"] += 1

    pairs = ["BTC-USDT", "ETH-USDT", "SOL-USDT", "XRP-USDT", "DOGE-USDT"]
    exchanges = ["OKX", "Binance", "Bybit", "Kraken", "Coinbase"]

    opportunities = []
    rng = random.Random()

    for pair in pairs:
        # Simulate price differences
        base_price = rng.uniform(0.1, 70000)
        spread_pct = rng.uniform(-0.5, 2.0)

        if spread_pct > 0.1:  # Only show meaningful spreads
            buy_exchange = rng.choice(exchanges)
            sell_exchange = rng.choice([e for e in exchanges if e != buy_exchange])
            buy_price = round(base_price, 6)
            sell_price = round(base_price * (1 + spread_pct / 100), 6)

            opp = {
                "id": str(uuid.uuid4())[:8],
                "pair": pair,
                "buy_exchange": buy_exchange,
                "sell_exchange": sell_exchange,
                "buy_price": buy_price,
                "sell_price": sell_price,
                "spread_pct": round(spread_pct, 4),
                "estimated_profit_pct": round(spread_pct - 0.1, 4),  # minus fees
                "confidence": round(rng.uniform(0.5, 0.99), 2),
                "expires_at": _utc_now(),
                "status": "active",
            }
            opportunities.append(opp)

    _stats["opportunities_found"] += len(opportunities)
    return opportunities


# ─── Endpoints ───────────────────────────────────────────────────────

@router.get("/")
def arbitraje_root(user: dict = Depends(get_current_user)):
    return {"message": "Arbitraje module active", "user": user.get("sub")}


@router.get("/opportunities")
async def get_opportunities(
    pair: Optional[str] = None,
    min_spread: float = 0.0,
    user: dict = Depends(get_current_user),
):
    """
    Scan and return current arbitrage opportunities.
    Optionally filter by trading pair or minimum spread.
    """
    opportunities = _scan_opportunities()

    if pair:
        opportunities = [o for o in opportunities if o["pair"] == pair.upper()]

    if min_spread > 0:
        opportunities = [o for o in opportunities if o["spread_pct"] >= min_spread]

    # Sort by estimated profit descending
    opportunities.sort(key=lambda x: x["estimated_profit_pct"], reverse=True)

    # Cache for execution reference
    _opportunities.clear()
    _opportunities.extend(opportunities)

    return {
        "opportunities": opportunities,
        "total": len(opportunities),
        "scanned_at": _utc_now(),
    }


@router.post("/execute")
async def execute_arbitrage(request: ArbitrageExecuteRequest, user: dict = Depends(get_current_user)):
    """
    Execute an arbitrage trade on a given opportunity.
    Requires confirm=True as a safety check.
    """
    if not request.confirm:
        raise HTTPException(
            status_code=400,
            detail="Set confirm=True to execute. This is a safety check.",
        )

    # Find the opportunity
    opp = None
    for o in _opportunities:
        if o["id"] == request.opportunity_id:
            opp = o
            break

    if not opp:
        raise HTTPException(status_code=404, detail=f"Opportunity '{request.opportunity_id}' not found or expired.")

    # Simulate execution
    user_id = user.get("sub", "anonymous")
    success = random.random() > 0.15  # 85% success rate simulation
    profit = round(request.amount * (opp["estimated_profit_pct"] / 100), 6) if success else 0.0

    trade = {
        "trade_id": str(uuid.uuid4())[:10],
        "opportunity_id": opp["id"],
        "user_id": user_id,
        "pair": opp["pair"],
        "buy_exchange": opp["buy_exchange"],
        "sell_exchange": opp["sell_exchange"],
        "amount": request.amount,
        "buy_price": opp["buy_price"],
        "sell_price": opp["sell_price"],
        "profit": profit,
        "success": success,
        "status": "completed" if success else "failed",
        "executed_at": _utc_now(),
    }

    _trade_history.append(trade)
    _stats["trades_executed"] += 1
    if success:
        _stats["successful_trades"] += 1
        _stats["total_profit"] += profit

    return {
        "success": success,
        "trade": trade,
        "message": "Trade executed successfully." if success else "Trade failed. Market conditions changed.",
    }


@router.get("/history")
async def get_trade_history(limit: int = 20, user: dict = Depends(get_current_user)):
    """Get the history of executed arbitrage trades."""
    user_id = user.get("sub", "anonymous")

    # Filter to user's trades
    user_trades = [t for t in _trade_history if t["user_id"] == user_id]
    recent = user_trades[-limit:]
    recent.reverse()

    return {
        "trades": recent,
        "total": len(user_trades),
        "returned": len(recent),
    }


@router.get("/stats")
async def get_stats(user: dict = Depends(get_current_user)):
    """Get arbitrage module statistics."""
    return {
        "stats": _stats,
        "total_trades_in_history": len(_trade_history),
        "timestamp": _utc_now(),
    }
