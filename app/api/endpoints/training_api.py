"""
Training API - Manage RL / ML training runs: start, stop, monitor metrics,
and review history.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/training", tags=["Training"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class TrainingConfig(BaseModel):
    algorithm: str = "PPO"
    learning_rate: float = Field(3e-4, gt=0)
    batch_size: int = Field(64, ge=1)
    epochs: int = Field(100, ge=1)
    gamma: float = Field(0.99, ge=0.0, le=1.0)
    environment: str = "crypto_trading"
    reward_function: str = "sharpe_ratio"
    params: dict = Field(default_factory=dict)


class TrainingStartRequest(BaseModel):
    config: TrainingConfig = Field(default_factory=TrainingConfig)


# ---------------------------------------------------------------------------
# In-memory state
# ---------------------------------------------------------------------------

_runs: Dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/start")
async def start_training(request: TrainingStartRequest):
    """Start a new training run."""
    run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    run = {
        "id": run_id,
        "status": "running",
        "config": request.config.model_dump(),
        "current_epoch": 0,
        "total_epochs": request.config.epochs,
        "metrics": [],
        "started_at": now,
        "stopped_at": None,
    }
    _runs[run_id] = run
    return {"status": "training_started", "run_id": run_id, "timestamp": now}


@router.get("/status")
async def training_status(run_id: Optional[str] = None):
    """Get status of a training run or all runs."""
    if run_id:
        run = _runs.get(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Training run not found")

        # Simulate progress
        if run["status"] == "running":
            import random
            run["current_epoch"] = min(run["current_epoch"] + max(1, run["total_epochs"] // 10), run["total_epochs"])
            metric = {
                "epoch": run["current_epoch"],
                "loss": round(random.uniform(0.01, 0.5), 4),
                "reward_mean": round(random.uniform(-1, 10), 4),
                "reward_std": round(random.uniform(0.1, 3), 4),
                "entropy": round(random.uniform(0.1, 2.0), 4),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            run["metrics"].append(metric)

            if run["current_epoch"] >= run["total_epochs"]:
                run["status"] = "completed"
                run["stopped_at"] = datetime.now(timezone.utc).isoformat()

        progress_pct = round((run["current_epoch"] / run["total_epochs"]) * 100, 1) if run["total_epochs"] > 0 else 0
        return {
            "run_id": run["id"],
            "status": run["status"],
            "progress": f"{progress_pct}%",
            "current_epoch": run["current_epoch"],
            "total_epochs": run["total_epochs"],
            "latest_metric": run["metrics"][-1] if run["metrics"] else None,
        }

    return {
        "total_runs": len(_runs),
        "running": sum(1 for r in _runs.values() if r["status"] == "running"),
        "completed": sum(1 for r in _runs.values() if r["status"] == "completed"),
        "runs": [
            {"id": r["id"], "status": r["status"], "algorithm": r["config"]["algorithm"]}
            for r in _runs.values()
        ],
    }


@router.post("/stop")
async def stop_training(run_id: str):
    """Stop a running training run."""
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Training run not found")
    if run["status"] != "running":
        raise HTTPException(status_code=409, detail=f"Run is {run['status']}, not running")

    run["status"] = "stopped"
    run["stopped_at"] = datetime.now(timezone.utc).isoformat()
    return {"status": "stopped", "run_id": run_id, "epochs_completed": run["current_epoch"]}


@router.get("/metrics")
async def training_metrics(run_id: str):
    """Return all recorded metrics for a training run."""
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Training run not found")

    return {
        "run_id": run_id,
        "status": run["status"],
        "metric_count": len(run["metrics"]),
        "metrics": run["metrics"],
    }


@router.get("/history")
async def training_history(
    limit: int = Query(20, ge=1, le=200),
    status: Optional[str] = Query(None, description="Filter by status"),
):
    """Return historical training runs."""
    results = list(_runs.values())
    if status:
        results = [r for r in results if r["status"] == status]

    results.sort(key=lambda r: r["started_at"], reverse=True)
    page = results[:limit]

    return {
        "total": len(results),
        "limit": limit,
        "history": [
            {
                "id": r["id"],
                "algorithm": r["config"]["algorithm"],
                "environment": r["config"]["environment"],
                "status": r["status"],
                "epochs": f"{r['current_epoch']}/{r['total_epochs']}",
                "started_at": r["started_at"],
                "stopped_at": r["stopped_at"],
            }
            for r in page
        ],
    }
