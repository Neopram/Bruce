# Distributed backtest executor (in-memory, no Ray dependency)
import time
import uuid
import threading
from enum import Enum


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DistributedExecutor:
    """In-memory distributed backtest executor with a thread-based job queue."""

    def __init__(self, max_workers=4):
        self._jobs = {}
        self._results = {}
        self._max_workers = max_workers
        self._lock = threading.Lock()

    def submit_backtest(self, strategy, data, config=None):
        """Submit a backtest job for execution.

        Args:
            strategy: Dict with 'name' and 'params' describing the trading strategy.
            data: Dict with 'symbol', 'timeframe', and 'candles' (list of OHLCV dicts).
            config: Optional dict with 'initial_capital', 'commission', 'slippage'.

        Returns:
            Dict with job_id and status.
        """
        job_id = str(uuid.uuid4())[:12]
        config = config or {}

        job = {
            "job_id": job_id,
            "strategy": strategy,
            "data_summary": {
                "symbol": data.get("symbol", "UNKNOWN"),
                "candles_count": len(data.get("candles", [])),
                "timeframe": data.get("timeframe", "1d"),
            },
            "config": {
                "initial_capital": config.get("initial_capital", 100000),
                "commission": config.get("commission", 0.001),
                "slippage": config.get("slippage", 0.0005),
            },
            "status": JobStatus.PENDING.value,
            "submitted_at": time.time(),
            "started_at": None,
            "completed_at": None,
        }

        with self._lock:
            self._jobs[job_id] = job

        thread = threading.Thread(target=self._run_backtest, args=(job_id, strategy, data, job["config"]), daemon=True)
        thread.start()

        return {"job_id": job_id, "status": "submitted"}

    def _run_backtest(self, job_id, strategy, data, config):
        """Execute a backtest simulation in background."""
        with self._lock:
            self._jobs[job_id]["status"] = JobStatus.RUNNING.value
            self._jobs[job_id]["started_at"] = time.time()

        try:
            candles = data.get("candles", [])
            capital = config["initial_capital"]
            commission = config["commission"]
            position = 0
            trades = []
            equity_curve = [capital]

            for i, candle in enumerate(candles):
                price = candle.get("close", 0)
                if price <= 0:
                    continue
                # Simple momentum strategy simulation
                if i > 0 and candle.get("close", 0) > candles[i - 1].get("close", 0) and position == 0:
                    shares = int(capital * 0.95 / price)
                    if shares > 0:
                        cost = shares * price * (1 + commission)
                        capital -= cost
                        position = shares
                        trades.append({"type": "buy", "price": price, "shares": shares, "bar": i})
                elif position > 0 and i > 0 and candle.get("close", 0) < candles[i - 1].get("close", 0):
                    proceeds = position * price * (1 - commission)
                    capital += proceeds
                    trades.append({"type": "sell", "price": price, "shares": position, "bar": i})
                    position = 0
                equity_curve.append(capital + position * price)

            final_equity = capital + position * (candles[-1].get("close", 0) if candles else 0)
            initial = config["initial_capital"]
            total_return = (final_equity - initial) / initial if initial > 0 else 0

            result = {
                "job_id": job_id,
                "strategy": strategy.get("name", "unknown"),
                "symbol": data.get("symbol", "UNKNOWN"),
                "total_return": round(total_return, 4),
                "final_equity": round(final_equity, 2),
                "num_trades": len(trades),
                "trades": trades[-10:],  # last 10 trades
                "equity_curve_length": len(equity_curve),
            }

            with self._lock:
                self._results[job_id] = result
                self._jobs[job_id]["status"] = JobStatus.COMPLETED.value
                self._jobs[job_id]["completed_at"] = time.time()

        except Exception as e:
            with self._lock:
                self._jobs[job_id]["status"] = JobStatus.FAILED.value
                self._jobs[job_id]["completed_at"] = time.time()
                self._results[job_id] = {"job_id": job_id, "error": str(e)}

    def get_status(self, job_id):
        """Check the status of a job."""
        with self._lock:
            job = self._jobs.get(job_id)
        if not job:
            return {"error": f"Job '{job_id}' not found"}
        return {
            "job_id": job_id,
            "status": job["status"],
            "submitted_at": job["submitted_at"],
            "started_at": job["started_at"],
            "completed_at": job["completed_at"],
        }

    def get_results(self, job_id):
        """Get results for a completed job."""
        with self._lock:
            job = self._jobs.get(job_id)
            result = self._results.get(job_id)
        if not job:
            return {"error": f"Job '{job_id}' not found"}
        if job["status"] != JobStatus.COMPLETED.value and job["status"] != JobStatus.FAILED.value:
            return {"error": "Job not yet completed", "status": job["status"]}
        return result

    def list_jobs(self):
        """List all jobs with their current status."""
        with self._lock:
            return [
                {
                    "job_id": jid,
                    "status": job["status"],
                    "strategy": job["strategy"].get("name", "unknown"),
                    "symbol": job["data_summary"]["symbol"],
                    "submitted_at": job["submitted_at"],
                }
                for jid, job in self._jobs.items()
            ]

    def cancel_job(self, job_id):
        """Cancel a pending job."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return {"error": f"Job '{job_id}' not found"}
            if job["status"] == JobStatus.PENDING.value:
                job["status"] = JobStatus.CANCELLED.value
                return {"job_id": job_id, "status": "cancelled"}
            return {"error": f"Cannot cancel job in '{job['status']}' state"}
