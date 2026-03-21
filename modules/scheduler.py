"""
Bruce AI - Autonomous Task Scheduler

Async task scheduler using asyncio for recurring and one-shot tasks.
Includes default Bruce monitoring tasks (market, news, health, reflection)
and integrates with the autonomy_core watcher system.
"""

import asyncio
import logging
import time
import traceback
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Union

logger = logging.getLogger("Bruce.Scheduler")

# ---------------------------------------------------------------------------
# Optional imports for default tasks
# ---------------------------------------------------------------------------

try:
    import requests as http_requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False
    logger.debug("feedparser not installed - news_digest task limited. Install: pip install feedparser")


# ---------------------------------------------------------------------------
# Task definitions
# ---------------------------------------------------------------------------

class TaskState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduledTask:
    """Metadata and state for a single scheduled task."""

    def __init__(
        self,
        name: str,
        callback: Callable,
        interval_seconds: float = 0,
        one_shot: bool = False,
        delay_seconds: float = 0,
    ):
        self.name = name
        self.callback = callback
        self.interval_seconds = interval_seconds
        self.one_shot = one_shot
        self.delay_seconds = delay_seconds
        self.state = TaskState.PENDING
        self.run_count = 0
        self.last_run: Optional[str] = None
        self.last_result: Any = None
        self.last_error: Optional[str] = None
        self.created_at = datetime.now(timezone.utc).isoformat()
        self._handle: Optional[asyncio.Task] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "interval_seconds": self.interval_seconds,
            "one_shot": self.one_shot,
            "run_count": self.run_count,
            "last_run": self.last_run,
            "last_error": self.last_error,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class BruceScheduler:
    """Async task scheduler for Bruce AI autonomous operations."""

    def __init__(self):
        self._tasks: Dict[str, ScheduledTask] = {}
        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._alerts: List[Dict[str, Any]] = []
        self._log: List[Dict[str, Any]] = []
        self._telegram_token: Optional[str] = None
        self._telegram_chat_id: Optional[str] = None

    # ----- configuration -------------------------------------------------

    def configure_telegram(self, token: str, chat_id: str):
        """Configure Telegram alerts (optional)."""
        self._telegram_token = token
        self._telegram_chat_id = chat_id
        logger.info("Telegram alerts configured for chat %s", chat_id)

    # ----- task registration ---------------------------------------------

    def schedule_recurring(
        self,
        name: str,
        interval_seconds: float,
        callback: Callable,
    ) -> Dict[str, Any]:
        """Register a recurring task that runs every interval_seconds."""
        if name in self._tasks:
            self.cancel_task(name)

        task = ScheduledTask(
            name=name,
            callback=callback,
            interval_seconds=interval_seconds,
            one_shot=False,
        )
        self._tasks[name] = task
        logger.info("Scheduled recurring task '%s' every %ds", name, interval_seconds)

        # If scheduler is already running, start this task immediately
        if self._running:
            self._launch_task(task)

        return {"scheduled": name, "interval": interval_seconds, "type": "recurring"}

    def schedule_once(
        self,
        name: str,
        delay_seconds: float,
        callback: Callable,
    ) -> Dict[str, Any]:
        """Register a one-shot task that runs once after delay_seconds."""
        if name in self._tasks:
            self.cancel_task(name)

        task = ScheduledTask(
            name=name,
            callback=callback,
            delay_seconds=delay_seconds,
            one_shot=True,
        )
        self._tasks[name] = task
        logger.info("Scheduled one-shot task '%s' in %ds", name, delay_seconds)

        if self._running:
            self._launch_task(task)

        return {"scheduled": name, "delay": delay_seconds, "type": "once"}

    def cancel_task(self, name: str) -> Dict[str, Any]:
        """Cancel a scheduled task."""
        task = self._tasks.get(name)
        if task is None:
            return {"status": "not_found", "name": name}
        if task._handle and not task._handle.done():
            task._handle.cancel()
        task.state = TaskState.CANCELLED
        del self._tasks[name]
        logger.info("Cancelled task '%s'", name)
        return {"status": "cancelled", "name": name}

    def list_tasks(self) -> List[Dict[str, Any]]:
        """List all registered tasks with their current state."""
        return [t.to_dict() for t in self._tasks.values()]

    # ----- start / stop --------------------------------------------------

    async def start(self):
        """Start the scheduler and launch all registered tasks."""
        if self._running:
            logger.warning("Scheduler already running")
            return
        self._running = True
        self._loop = asyncio.get_event_loop()
        logger.info("Bruce Scheduler started with %d tasks", len(self._tasks))
        for task in self._tasks.values():
            self._launch_task(task)

    async def stop(self):
        """Stop the scheduler and cancel all running tasks."""
        self._running = False
        for task in self._tasks.values():
            if task._handle and not task._handle.done():
                task._handle.cancel()
            task.state = TaskState.CANCELLED
        logger.info("Bruce Scheduler stopped")

    def _launch_task(self, task: ScheduledTask):
        """Create an asyncio Task for a ScheduledTask."""
        if task.one_shot:
            task._handle = asyncio.ensure_future(self._run_once(task))
        else:
            task._handle = asyncio.ensure_future(self._run_recurring(task))

    # ----- internal runners ----------------------------------------------

    async def _run_recurring(self, task: ScheduledTask):
        """Run a task on a recurring interval."""
        try:
            while self._running and task.name in self._tasks:
                await self._execute(task)
                await asyncio.sleep(task.interval_seconds)
        except asyncio.CancelledError:
            task.state = TaskState.CANCELLED
        except Exception as e:
            logger.error("Recurring task '%s' crashed: %s", task.name, e)
            task.state = TaskState.FAILED
            task.last_error = str(e)

    async def _run_once(self, task: ScheduledTask):
        """Run a task once after a delay."""
        try:
            if task.delay_seconds > 0:
                await asyncio.sleep(task.delay_seconds)
            await self._execute(task)
            task.state = TaskState.COMPLETED
        except asyncio.CancelledError:
            task.state = TaskState.CANCELLED
        except Exception as e:
            logger.error("One-shot task '%s' failed: %s", task.name, e)
            task.state = TaskState.FAILED
            task.last_error = str(e)

    async def _execute(self, task: ScheduledTask):
        """Execute a task callback (sync or async)."""
        task.state = TaskState.RUNNING
        task.last_run = datetime.now(timezone.utc).isoformat()
        task.run_count += 1

        try:
            start = time.perf_counter()
            if asyncio.iscoroutinefunction(task.callback):
                result = await task.callback()
            else:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, task.callback)
            elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

            task.last_result = result
            task.last_error = None
            if not task.one_shot:
                task.state = TaskState.PENDING

            log_entry = {
                "task": task.name,
                "status": "success",
                "elapsed_ms": elapsed_ms,
                "timestamp": task.last_run,
            }
            self._log.append(log_entry)
            logger.debug("Task '%s' completed in %.1fms", task.name, elapsed_ms)

            # Check if result contains an alert
            if isinstance(result, dict) and result.get("alert"):
                await self._send_alert(task.name, result["alert"])

        except Exception as e:
            task.last_error = str(e)
            task.state = TaskState.FAILED if task.one_shot else TaskState.PENDING
            self._log.append({
                "task": task.name,
                "status": "error",
                "error": str(e),
                "timestamp": task.last_run,
            })
            logger.warning("Task '%s' error: %s", task.name, e)

    # ----- alerts --------------------------------------------------------

    async def _send_alert(self, task_name: str, message: str):
        """Send an alert via Telegram if configured, otherwise just log it."""
        alert = {
            "task": task_name,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._alerts.append(alert)
        logger.info("ALERT [%s]: %s", task_name, message)

        if self._telegram_token and self._telegram_chat_id and REQUESTS_AVAILABLE:
            try:
                url = f"https://api.telegram.org/bot{self._telegram_token}/sendMessage"
                payload = {
                    "chat_id": self._telegram_chat_id,
                    "text": f"Bruce Alert [{task_name}]\n{message}",
                    "parse_mode": "Markdown",
                }
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: http_requests.post(url, json=payload, timeout=10),
                )
            except Exception as e:
                logger.warning("Telegram alert failed: %s", e)

    # ----- status --------------------------------------------------------

    def get_alerts(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self._alerts[-limit:]

    def get_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._log[-limit:]

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "tasks": len(self._tasks),
            "total_runs": sum(t.run_count for t in self._tasks.values()),
            "alerts": len(self._alerts),
            "task_list": self.list_tasks(),
        }


# ---------------------------------------------------------------------------
# Default Bruce tasks
# ---------------------------------------------------------------------------

def _market_check() -> Dict[str, Any]:
    """Check BTC/ETH/SOL prices from CoinGecko public API."""
    if not REQUESTS_AVAILABLE:
        return {"status": "skipped", "reason": "requests not installed"}

    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin,ethereum,solana",
            "vs_currencies": "usd",
            "include_24hr_change": "true",
        }
        resp = http_requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            return {"status": "error", "http_status": resp.status_code}
        data = resp.json()

        prices = {}
        alert_msg = None
        for coin_id, coin_data in data.items():
            price = coin_data.get("usd", 0)
            change = coin_data.get("usd_24h_change", 0)
            prices[coin_id] = {"usd": price, "change_24h": round(change, 2) if change else 0}
            # Alert on large moves
            if abs(change or 0) > 5:
                alert_msg = (alert_msg or "") + f"{coin_id}: ${price:,.0f} ({change:+.1f}%)\n"

        result = {"status": "ok", "prices": prices, "timestamp": datetime.now(timezone.utc).isoformat()}
        if alert_msg:
            result["alert"] = f"Significant price movement:\n{alert_msg}"
        return result
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _news_digest() -> Dict[str, Any]:
    """Aggregate latest news from RSS feeds."""
    feeds = [
        "https://feeds.feedburner.com/CoinDesk",
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
    ]

    articles = []
    if FEEDPARSER_AVAILABLE:
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:5]:
                    articles.append({
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "published": entry.get("published", ""),
                        "source": feed.feed.get("title", feed_url),
                    })
            except Exception as e:
                logger.debug("Feed parse error for %s: %s", feed_url, e)
    elif REQUESTS_AVAILABLE:
        # Minimal fallback: just check if feeds are reachable
        for feed_url in feeds:
            try:
                resp = http_requests.get(feed_url, timeout=10)
                if resp.status_code == 200:
                    articles.append({"source": feed_url, "status": "reachable"})
            except Exception:
                pass

    return {
        "status": "ok",
        "articles_found": len(articles),
        "articles": articles[:15],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _self_reflect() -> Dict[str, Any]:
    """Bruce self-reflection - review performance metrics."""
    try:
        from modules.autonomy_core import AutonomyCore
        core = AutonomyCore()
        status = core.get_status()
        history = core.get_execution_history(limit=10)

        total = len(history)
        successes = sum(1 for h in history if h.get("status") == "completed")
        failures = sum(1 for h in history if h.get("status") == "failed")

        reflection = {
            "status": "ok",
            "autonomous_mode": status.get("autonomous_mode"),
            "recent_executions": total,
            "success_rate": round(successes / max(total, 1) * 100, 1),
            "failures": failures,
            "pending_reviews": status.get("pending_reviews", 0),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if failures > total * 0.3 and total > 3:
            reflection["alert"] = (
                f"High failure rate: {failures}/{total} recent actions failed. "
                f"Success rate: {reflection['success_rate']}%"
            )
        return reflection
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _health_check() -> Dict[str, Any]:
    """System health check - verify critical services."""
    health = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {},
    }

    # Check Ollama
    if REQUESTS_AVAILABLE:
        try:
            resp = http_requests.get("http://localhost:11434/api/tags", timeout=3)
            health["checks"]["ollama"] = "ok" if resp.status_code == 200 else "down"
        except Exception:
            health["checks"]["ollama"] = "unreachable"

    # Check ChromaDB
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(
            __import__("pathlib").Path(__file__).resolve().parent.parent / "data" / "vector_memory" / "chromadb"
        ))
        collections = client.list_collections()
        health["checks"]["chromadb"] = f"ok ({len(collections)} collections)"
    except Exception as e:
        health["checks"]["chromadb"] = f"error: {e}"

    # Check memory usage (basic)
    try:
        import os
        if hasattr(os, "getloadavg"):
            load = os.getloadavg()
            health["checks"]["load_avg"] = {"1m": load[0], "5m": load[1], "15m": load[2]}
        else:
            # Windows fallback
            import psutil
            health["checks"]["cpu_percent"] = psutil.cpu_percent(interval=0.1)
            health["checks"]["memory_percent"] = psutil.virtual_memory().percent
    except ImportError:
        health["checks"]["system"] = "psutil not available"
    except Exception:
        pass

    # Overall status
    critical_down = any(
        v in ("down", "unreachable")
        for v in health["checks"].values()
        if isinstance(v, str)
    )
    health["status"] = "degraded" if critical_down else "ok"

    if critical_down:
        down_services = [
            k for k, v in health["checks"].items()
            if isinstance(v, str) and v in ("down", "unreachable")
        ]
        health["alert"] = f"Services down: {', '.join(down_services)}"

    return health


# ---------------------------------------------------------------------------
# Factory: create a scheduler with default Bruce tasks
# ---------------------------------------------------------------------------

def create_default_scheduler() -> BruceScheduler:
    """Create a BruceScheduler pre-loaded with default autonomous tasks."""
    scheduler = BruceScheduler()

    scheduler.schedule_recurring("health_check", 60, _health_check)          # every 1 min
    scheduler.schedule_recurring("market_check", 300, _market_check)         # every 5 min
    scheduler.schedule_recurring("news_digest", 3600, _news_digest)          # every 1 hour
    scheduler.schedule_recurring("self_reflect", 21600, _self_reflect)       # every 6 hours

    return scheduler


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_scheduler: Optional[BruceScheduler] = None


def get_scheduler() -> BruceScheduler:
    """Get or create the singleton scheduler with default tasks."""
    global _scheduler
    if _scheduler is None:
        _scheduler = create_default_scheduler()
    return _scheduler


async def start_scheduler():
    """Convenience: get the singleton scheduler and start it."""
    scheduler = get_scheduler()
    await scheduler.start()
    return scheduler


async def stop_scheduler():
    """Convenience: stop the singleton scheduler."""
    if _scheduler is not None:
        await _scheduler.stop()
