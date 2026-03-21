"""
Episodes API - CRUD and statistics for reinforcement-learning episodes.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/episodes", tags=["Episodes"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class EpisodeStep(BaseModel):
    step: int
    state: dict = Field(default_factory=dict)
    action: str = ""
    reward: float = 0.0
    done: bool = False


class EpisodeCreate(BaseModel):
    agent_id: str = "default"
    environment: str = "crypto_trading"
    steps: List[EpisodeStep] = Field(default_factory=list)
    total_reward: float = 0.0
    metadata: dict = Field(default_factory=dict)


class EpisodeRecord(BaseModel):
    id: str
    agent_id: str
    environment: str
    steps: List[EpisodeStep]
    total_reward: float
    step_count: int
    metadata: dict
    created_at: str


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

_episodes: List[dict] = []


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("")
async def list_episodes(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    environment: Optional[str] = Query(None, description="Filter by environment"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List stored RL episodes with optional filters."""
    results = _episodes

    if agent_id:
        results = [e for e in results if e["agent_id"] == agent_id]
    if environment:
        results = [e for e in results if e["environment"] == environment]

    total = len(results)
    page = results[offset: offset + limit]
    return {"status": "success", "total": total, "offset": offset, "limit": limit, "data": page}


@router.get("/stats")
async def episode_stats(agent_id: Optional[str] = Query(None)):
    """Return aggregate statistics across stored episodes."""
    subset = _episodes
    if agent_id:
        subset = [e for e in subset if e["agent_id"] == agent_id]

    if not subset:
        return {
            "total_episodes": 0,
            "avg_reward": 0.0,
            "max_reward": 0.0,
            "min_reward": 0.0,
            "avg_steps": 0.0,
        }

    rewards = [e["total_reward"] for e in subset]
    steps = [e["step_count"] for e in subset]

    return {
        "total_episodes": len(subset),
        "avg_reward": round(sum(rewards) / len(rewards), 4),
        "max_reward": round(max(rewards), 4),
        "min_reward": round(min(rewards), 4),
        "avg_steps": round(sum(steps) / len(steps), 2),
        "environments": list({e["environment"] for e in subset}),
        "agents": list({e["agent_id"] for e in subset}),
    }


@router.get("/{episode_id}")
async def get_episode(episode_id: str):
    """Get a specific episode by ID."""
    for ep in _episodes:
        if ep["id"] == episode_id:
            return {"status": "success", "data": ep}
    raise HTTPException(status_code=404, detail=f"Episode {episode_id} not found")


@router.post("", status_code=201)
async def store_episode(payload: EpisodeCreate):
    """Store a new RL episode."""
    record = {
        "id": str(uuid.uuid4()),
        "agent_id": payload.agent_id,
        "environment": payload.environment,
        "steps": [s.model_dump() for s in payload.steps],
        "total_reward": payload.total_reward,
        "step_count": len(payload.steps),
        "metadata": payload.metadata,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _episodes.append(record)
    return {"status": "created", "data": record}
