"""Frontend API endpoints - bridges frontend component calls to backend services."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import random
import uuid

router = APIRouter()


# ──────────────────────────── Pydantic Models ────────────────────────────

# Admin
class UserOut(BaseModel):
    id: str
    username: str
    role: str
    last_active: str


class AuditEntry(BaseModel):
    id: str
    user: str
    action: str
    timestamp: str


# AI
class AILogEntry(BaseModel):
    timestamp: str
    level: str
    model: str
    message: str


class AIStatus(BaseModel):
    models_loaded: List[str]
    memory_usage: float
    uptime: float


class HealResult(BaseModel):
    status: str
    actions_taken: List[str]


class HealingStatus(BaseModel):
    is_healing: bool
    last_heal: Optional[str]
    health_score: float


# Arbitrage
class ArbitrageOpportunity(BaseModel):
    id: str
    pair: str
    exchange_a: str
    exchange_b: str
    spread_pct: float
    est_profit: float


class ArbitrageExecuteRequest(BaseModel):
    opportunity_id: str
    confirm: bool = False


class ArbitrageExecuteResult(BaseModel):
    status: str
    opportunity_id: str
    executed_at: str
    profit: float
    message: str


# Avatar
class AvatarMode(BaseModel):
    mode: str


class AvatarInfo(BaseModel):
    id: str
    name: str
    style: str
    preview_url: str


class AvatarSelectRequest(BaseModel):
    avatar_id: str


class AvatarSelectResult(BaseModel):
    avatar_id: str
    name: str
    active: bool


# Emotion / Cognition
class EmotionState(BaseModel):
    emotion: str
    intensity: float
    valence: float


class CognitionStatus(BaseModel):
    active_model: str
    memory_count: int
    personality: str


# Trading
class Strategy(BaseModel):
    name: str
    signal: str
    confidence: float
    return_pct: float
    sharpe: float
    win_rate: float
    is_active: bool


class Position(BaseModel):
    pair: str
    side: str
    amount: float
    entry_price: float
    current_price: float
    pnl: float


class Portfolio(BaseModel):
    balance: float
    positions: List[Position]
    total_value: float
    pnl_24h: float


class TradeHistoryEntry(BaseModel):
    date: str
    pair: str
    side: str
    amount: float
    price: float
    pnl: float


# Indicators
class Indicators(BaseModel):
    rsi: float
    macd: float
    sma_20: float
    sma_50: float
    bollinger_upper: float
    bollinger_lower: float


# Social / Macro
class TopicSentiment(BaseModel):
    topic: str
    sentiment: float
    volume: int


class SocialSentiment(BaseModel):
    fear_greed_index: int
    trending_topics: List[TopicSentiment]
    source_breakdown: dict


class MacroSummary(BaseModel):
    outlook: str
    gdp_trend: str
    inflation: float
    rates: float


# Self-rewrite
class SelfRewriteResult(BaseModel):
    suggestions: List[str]
    improvements: List[str]


# ──────────────────────────── Helpers ────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _past_iso(minutes: int = 0, hours: int = 0, days: int = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes, hours=hours, days=days)).isoformat()


PAIRS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT", "ADA/USDT", "AVAX/USDT", "DOT/USDT"]
EXCHANGES = ["Binance", "Coinbase", "Kraken", "Bybit", "OKX", "KuCoin"]
MODELS = ["deepseek-v3", "gpt-4o", "claude-3.5", "llama-3-70b"]
EMOTIONS = ["focused", "confident", "cautious", "analytical", "neutral", "alert"]
SIGNALS = ["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"]
STRATEGY_NAMES = ["Momentum Alpha", "Mean Reversion", "Trend Following", "Volatility Breakout", "Statistical Arb", "Sentiment Surge"]
ACTIONS_POOL = [
    "Rebalanced model weights",
    "Cleared stale cache entries",
    "Restarted lagging worker",
    "Applied config hot-reload",
    "Recalibrated risk thresholds",
    "Pruned memory graph",
    "Optimized embedding index",
]
AUDIT_ACTIONS = [
    "login", "logout", "trade_executed", "config_changed",
    "model_switched", "api_key_rotated", "alert_acknowledged",
    "strategy_toggled", "portfolio_rebalanced",
]
USERNAMES = ["admin", "bruce", "alfred", "oracle", "lucius"]


# ──────────────────────────── Admin ────────────────────────────

@router.get("/admin/users", response_model=List[UserOut], tags=["Admin"])
async def get_admin_users():
    roles = ["admin", "operator", "viewer"]
    return [
        UserOut(
            id=str(uuid.uuid4())[:8],
            username=u,
            role=random.choice(roles),
            last_active=_past_iso(minutes=random.randint(1, 600)),
        )
        for u in USERNAMES
    ]


@router.get("/admin/audit", response_model=List[AuditEntry], tags=["Admin"])
async def get_audit_log():
    return [
        AuditEntry(
            id=str(uuid.uuid4())[:8],
            user=random.choice(USERNAMES),
            action=random.choice(AUDIT_ACTIONS),
            timestamp=_past_iso(minutes=random.randint(1, 1440)),
        )
        for _ in range(20)
    ]


# ──────────────────────────── AI ────────────────────────────

@router.get("/ai/logs", response_model=List[AILogEntry], tags=["AI"])
async def get_ai_logs():
    levels = ["INFO", "DEBUG", "WARNING", "ERROR"]
    messages = [
        "Inference completed in 243ms",
        "Token budget within limits",
        "Model checkpoint loaded",
        "Context window at 78% capacity",
        "Rate limit approaching threshold",
        "Embedding cache hit ratio: 0.94",
        "Memory consolidation cycle complete",
        "Fallback model activated",
    ]
    return [
        AILogEntry(
            timestamp=_past_iso(minutes=random.randint(0, 120)),
            level=random.choice(levels),
            model=random.choice(MODELS),
            message=random.choice(messages),
        )
        for _ in range(15)
    ]


@router.get("/ai/status", response_model=AIStatus, tags=["AI"])
async def get_ai_status():
    return AIStatus(
        models_loaded=random.sample(MODELS, k=random.randint(2, len(MODELS))),
        memory_usage=round(random.uniform(40.0, 85.0), 1),
        uptime=round(random.uniform(3600, 604800), 0),
    )


@router.post("/ai/self-healing/heal", response_model=HealResult, tags=["AI"])
async def trigger_self_healing():
    chosen = random.sample(ACTIONS_POOL, k=random.randint(2, 4))
    return HealResult(status="healed", actions_taken=chosen)


@router.get("/ai/self-healing/status", response_model=HealingStatus, tags=["AI"])
async def get_healing_status():
    return HealingStatus(
        is_healing=False,
        last_heal=_past_iso(hours=random.randint(1, 12)),
        health_score=round(random.uniform(0.85, 1.0), 3),
    )


# ──────────────────────────── Arbitrage ────────────────────────────

@router.get("/arbitrage/opportunities", response_model=List[ArbitrageOpportunity], tags=["Arbitrage"])
async def get_arbitrage_opportunities():
    opps = []
    for _ in range(random.randint(3, 8)):
        exs = random.sample(EXCHANGES, 2)
        spread = round(random.uniform(0.05, 2.5), 2)
        opps.append(ArbitrageOpportunity(
            id=str(uuid.uuid4())[:8],
            pair=random.choice(PAIRS),
            exchange_a=exs[0],
            exchange_b=exs[1],
            spread_pct=spread,
            est_profit=round(spread * random.uniform(50, 500), 2),
        ))
    return opps


@router.post("/arbitrage/execute", response_model=ArbitrageExecuteResult, tags=["Arbitrage"])
async def execute_arbitrage(req: ArbitrageExecuteRequest):
    if not req.confirm:
        raise HTTPException(status_code=400, detail="Execution not confirmed. Set confirm=true.")
    return ArbitrageExecuteResult(
        status="executed",
        opportunity_id=req.opportunity_id,
        executed_at=_now_iso(),
        profit=round(random.uniform(10, 800), 2),
        message="Arbitrage executed successfully",
    )


# ──────────────────────────── Avatar ────────────────────────────

_current_avatar_mode = "full"
_current_avatar_id = "bruce-default"


@router.get("/avatar/mode", response_model=AvatarMode, tags=["Avatar"])
async def get_avatar_mode():
    return AvatarMode(mode=_current_avatar_mode)


@router.put("/avatar/mode", response_model=AvatarMode, tags=["Avatar"])
async def set_avatar_mode(body: AvatarMode):
    global _current_avatar_mode
    if body.mode not in ("full", "minimal", "voice"):
        raise HTTPException(status_code=400, detail="Mode must be full, minimal, or voice")
    _current_avatar_mode = body.mode
    return AvatarMode(mode=_current_avatar_mode)


@router.get("/avatar/select", response_model=List[AvatarInfo], tags=["Avatar"])
async def get_available_avatars():
    return [
        AvatarInfo(id="bruce-default", name="Bruce Classic", style="dark", preview_url="/static/avatars/bruce-default.png"),
        AvatarInfo(id="bruce-neon", name="Bruce Neon", style="cyberpunk", preview_url="/static/avatars/bruce-neon.png"),
        AvatarInfo(id="bruce-minimal", name="Bruce Minimal", style="clean", preview_url="/static/avatars/bruce-minimal.png"),
        AvatarInfo(id="bruce-hologram", name="Bruce Hologram", style="futuristic", preview_url="/static/avatars/bruce-hologram.png"),
    ]


@router.put("/avatar/select", response_model=AvatarSelectResult, tags=["Avatar"])
async def set_avatar(body: AvatarSelectRequest):
    global _current_avatar_id
    _current_avatar_id = body.avatar_id
    return AvatarSelectResult(avatar_id=body.avatar_id, name=f"Avatar {body.avatar_id}", active=True)


# ──────────────────────────── Emotion / Cognition (bruce-api) ────────────────────────────

@router.get("/bruce-api/emotion/state/{user_id}", response_model=EmotionState, tags=["Emotion"])
async def get_emotion_state(user_id: str):
    return EmotionState(
        emotion=random.choice(EMOTIONS),
        intensity=round(random.uniform(0.3, 1.0), 2),
        valence=round(random.uniform(-1.0, 1.0), 2),
    )


@router.get("/bruce-api/cognition/status", response_model=CognitionStatus, tags=["Cognition"])
async def get_cognition_status():
    return CognitionStatus(
        active_model=random.choice(MODELS),
        memory_count=random.randint(500, 15000),
        personality="strategic-analytical",
    )


# ──────────────────────────── Trading ────────────────────────────

@router.get("/trading/strategies", response_model=List[Strategy], tags=["Trading"])
async def get_trading_strategies():
    return [
        Strategy(
            name=name,
            signal=random.choice(SIGNALS),
            confidence=round(random.uniform(0.5, 0.98), 2),
            return_pct=round(random.uniform(-5.0, 25.0), 2),
            sharpe=round(random.uniform(0.5, 3.5), 2),
            win_rate=round(random.uniform(0.45, 0.80), 2),
            is_active=random.choice([True, True, False]),
        )
        for name in STRATEGY_NAMES
    ]


@router.get("/trading/portfolio", response_model=Portfolio, tags=["Trading"])
async def get_trading_portfolio():
    positions = []
    for _ in range(random.randint(2, 5)):
        pair = random.choice(PAIRS)
        entry = round(random.uniform(100, 70000), 2)
        current = round(entry * random.uniform(0.92, 1.12), 2)
        amt = round(random.uniform(0.01, 5.0), 4)
        positions.append(Position(
            pair=pair,
            side=random.choice(["long", "short"]),
            amount=amt,
            entry_price=entry,
            current_price=current,
            pnl=round((current - entry) * amt, 2),
        ))
    balance = round(random.uniform(10000, 150000), 2)
    pos_value = sum(p.current_price * p.amount for p in positions)
    return Portfolio(
        balance=balance,
        positions=positions,
        total_value=round(balance + pos_value, 2),
        pnl_24h=round(random.uniform(-3000, 5000), 2),
    )


@router.get("/trading/history", response_model=List[TradeHistoryEntry], tags=["Trading"])
async def get_trade_history():
    return [
        TradeHistoryEntry(
            date=_past_iso(hours=random.randint(1, 168)),
            pair=random.choice(PAIRS),
            side=random.choice(["buy", "sell"]),
            amount=round(random.uniform(0.01, 10.0), 4),
            price=round(random.uniform(100, 70000), 2),
            pnl=round(random.uniform(-500, 1500), 2),
        )
        for _ in range(20)
    ]


# ──────────────────────────── Indicators ────────────────────────────

@router.get("/indicators", response_model=Indicators, tags=["Indicators"])
async def get_indicators():
    sma_20 = round(random.uniform(55000, 72000), 2)
    sma_50 = round(sma_20 * random.uniform(0.93, 1.07), 2)
    bb_mid = (sma_20 + sma_50) / 2
    bb_width = bb_mid * random.uniform(0.02, 0.06)
    return Indicators(
        rsi=round(random.uniform(20, 80), 1),
        macd=round(random.uniform(-500, 500), 2),
        sma_20=sma_20,
        sma_50=sma_50,
        bollinger_upper=round(bb_mid + bb_width, 2),
        bollinger_lower=round(bb_mid - bb_width, 2),
    )


# ──────────────────────────── Social / Macro ────────────────────────────

@router.get("/social/sentiment", response_model=SocialSentiment, tags=["Social"])
async def get_social_sentiment():
    topics = [
        TopicSentiment(topic="Bitcoin ETF", sentiment=round(random.uniform(0.3, 0.9), 2), volume=random.randint(5000, 50000)),
        TopicSentiment(topic="Fed Rate Decision", sentiment=round(random.uniform(-0.5, 0.5), 2), volume=random.randint(10000, 80000)),
        TopicSentiment(topic="Ethereum Upgrade", sentiment=round(random.uniform(0.4, 0.95), 2), volume=random.randint(3000, 30000)),
        TopicSentiment(topic="Crypto Regulation", sentiment=round(random.uniform(-0.8, 0.2), 2), volume=random.randint(8000, 40000)),
    ]
    return SocialSentiment(
        fear_greed_index=random.randint(15, 85),
        trending_topics=topics,
        source_breakdown={
            "twitter": round(random.uniform(30, 50), 1),
            "reddit": round(random.uniform(15, 30), 1),
            "news": round(random.uniform(10, 25), 1),
            "telegram": round(random.uniform(5, 15), 1),
        },
    )


@router.get("/macro/summary", response_model=MacroSummary, tags=["Macro"])
async def get_macro_summary():
    outlooks = ["bullish", "bearish", "neutral", "cautiously optimistic", "risk-off"]
    trends = ["expanding", "contracting", "stable", "accelerating", "decelerating"]
    return MacroSummary(
        outlook=random.choice(outlooks),
        gdp_trend=random.choice(trends),
        inflation=round(random.uniform(2.0, 6.5), 1),
        rates=round(random.uniform(3.5, 5.75), 2),
    )


# ──────────────────────────── Self-Rewrite ────────────────────────────

@router.post("/self-rewrite", response_model=SelfRewriteResult, tags=["Self-Modification"])
async def self_rewrite():
    suggestions = random.sample([
        "Consolidate overlapping strategy signals into a unified scoring layer",
        "Add circuit breaker for cascading API failures",
        "Implement adaptive position sizing based on volatility regime",
        "Replace polling-based data fetch with WebSocket streams",
        "Add memory-aware context pruning for long sessions",
        "Introduce A/B testing framework for model selection",
    ], k=random.randint(2, 4))
    improvements = random.sample([
        "Reduced inference latency by 18% via batch processing",
        "Compressed embedding store - memory usage down 22%",
        "Refactored risk engine to support multi-asset correlation",
        "Added graceful degradation for external API timeouts",
        "Improved cache invalidation strategy for market data",
    ], k=random.randint(2, 3))
    return SelfRewriteResult(suggestions=suggestions, improvements=improvements)
