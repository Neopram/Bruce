"""
Simulation API - Start, stop, configure, and retrieve results for
trading/market simulations.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/simulation", tags=["Simulation"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class SimulationConfig(BaseModel):
    initial_balance: float = Field(10000.0, gt=0)
    trading_pair: str = "BTC/USDT"
    strategy: str = "mean_reversion"
    timeframe: str = "1h"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    slippage_pct: float = Field(0.1, ge=0.0, le=5.0)
    commission_pct: float = Field(0.1, ge=0.0, le=5.0)
    params: dict = Field(default_factory=dict)


class SimulationStartRequest(BaseModel):
    config: SimulationConfig = Field(default_factory=SimulationConfig)


# ---------------------------------------------------------------------------
# In-memory state
# ---------------------------------------------------------------------------

_simulations: Dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/start")
async def start_simulation(request: SimulationStartRequest):
    """Start a new trading simulation."""
    sim_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    sim = {
        "id": sim_id,
        "status": "running",
        "config": request.config.model_dump(),
        "progress_pct": 0.0,
        "started_at": now,
        "stopped_at": None,
        "results": None,
    }
    _simulations[sim_id] = sim
    return {"status": "simulation_launched", "simulation_id": sim_id, "timestamp": now}


@router.get("/status")
async def simulation_status(simulation_id: Optional[str] = None):
    """Get simulation status. If no ID given, return all active simulations."""
    if simulation_id:
        sim = _simulations.get(simulation_id)
        if not sim:
            raise HTTPException(status_code=404, detail="Simulation not found")

        # Simulate progress advancement
        if sim["status"] == "running":
            sim["progress_pct"] = min(sim["progress_pct"] + 15.0, 100.0)
            if sim["progress_pct"] >= 100.0:
                sim["status"] = "completed"
                sim["stopped_at"] = datetime.now(timezone.utc).isoformat()
                sim["results"] = _generate_results(sim["config"])

        return sim

    active = [s for s in _simulations.values() if s["status"] == "running"]
    return {"active_count": len(active), "simulations": list(_simulations.values())}


@router.post("/stop")
async def stop_simulation(simulation_id: str):
    """Stop a running simulation."""
    sim = _simulations.get(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    if sim["status"] != "running":
        raise HTTPException(status_code=409, detail=f"Simulation is {sim['status']}, not running")

    sim["status"] = "stopped"
    sim["stopped_at"] = datetime.now(timezone.utc).isoformat()
    sim["results"] = _generate_results(sim["config"])
    return {"status": "stopped", "simulation_id": simulation_id}


@router.get("/results")
async def get_results(simulation_id: str):
    """Get results of a completed or stopped simulation."""
    sim = _simulations.get(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    if sim["status"] == "running":
        raise HTTPException(status_code=409, detail="Simulation is still running")

    return {
        "simulation_id": simulation_id,
        "status": sim["status"],
        "config": sim["config"],
        "results": sim["results"],
    }


@router.post("/config")
async def configure_simulation(config: SimulationConfig):
    """Validate and preview a simulation configuration (dry-run)."""
    return {
        "valid": True,
        "config": config.model_dump(),
        "estimated_duration_sec": 30,
        "message": "Configuration is valid. Call /simulation/start to begin.",
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_results(config: dict) -> dict:
    """Generate simulated backtest results."""
    import random

    initial = config.get("initial_balance", 10000)
    pnl_pct = round(random.uniform(-20, 40), 2)
    final = round(initial * (1 + pnl_pct / 100), 2)
    trades = random.randint(20, 200)
    win_rate = round(random.uniform(0.35, 0.7), 2)

    return {
        "initial_balance": initial,
        "final_balance": final,
        "pnl_pct": pnl_pct,
        "total_trades": trades,
        "win_rate": win_rate,
        "max_drawdown_pct": round(random.uniform(2, 25), 2),
        "sharpe_ratio": round(random.uniform(-0.5, 3.0), 2),
        "profit_factor": round(random.uniform(0.5, 3.0), 2),
    }
