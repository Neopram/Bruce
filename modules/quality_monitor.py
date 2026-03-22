"""
Bruce AI - Quality Monitor

Background service that periodically runs quick benchmarks and tracks
quality trends over time. Alerts when performance drops below thresholds.

Can run standalone or be integrated with Bruce's scheduler:
    python -m modules.quality_monitor              # run once
    python -m modules.quality_monitor --daemon      # run continuously
    python -m modules.quality_monitor --report      # show trend report
    python -m modules.quality_monitor --interval 4  # run every 4 hours
"""

import json
import logging
import os
import signal
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("Bruce.QualityMonitor")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "benchmarks"
TREND_FILE = DATA_DIR / "quality_trends.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Thresholds - alert when scores drop below these
# ---------------------------------------------------------------------------
DEFAULT_THRESHOLDS = {
    "knowledge": 60.0,       # % correct
    "hallucination": 50.0,   # % uncertainty admitted
    "latency_p50_max": 5.0,  # seconds
    "latency_p95_max": 15.0, # seconds
    "overall": 50.0,         # composite %
}

# ---------------------------------------------------------------------------
# Optional imports
# ---------------------------------------------------------------------------
try:
    from modules.benchmark import BenchmarkSuite, BenchmarkResult
    BENCHMARK_AVAILABLE = True
except Exception:
    BENCHMARK_AVAILABLE = False

try:
    from modules.llm_bridge import LLMBridge
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False

try:
    from modules.telegram_alerts import send_alert
    TELEGRAM_AVAILABLE = True
except Exception:
    TELEGRAM_AVAILABLE = False


# ============================================================================
# Trend Storage
# ============================================================================

def load_trends() -> List[Dict[str, Any]]:
    """Load historical trend data."""
    if TREND_FILE.exists():
        try:
            with open(TREND_FILE, "r") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception:
            return []
    return []


def save_trends(trends: List[Dict[str, Any]]) -> None:
    """Save trend data, keeping last 500 entries max."""
    trends = trends[-500:]
    with open(TREND_FILE, "w") as f:
        json.dump(trends, f, indent=2, default=str)


def append_trend(entry: Dict[str, Any]) -> None:
    """Append a single trend entry."""
    trends = load_trends()
    trends.append(entry)
    save_trends(trends)


# ============================================================================
# Alert System
# ============================================================================

class AlertManager:
    """Manages quality alerts via multiple channels."""

    def __init__(self, thresholds: Optional[Dict[str, float]] = None):
        self.thresholds = thresholds or DEFAULT_THRESHOLDS.copy()
        self.alert_history: List[Dict[str, Any]] = []

    def check(self, report: Dict[str, Any]) -> List[Dict[str, str]]:
        """Check benchmark report against thresholds. Returns list of alerts."""
        alerts = []
        benchmarks = report.get("benchmarks", {})

        # Knowledge accuracy
        knowledge = benchmarks.get("knowledge", {})
        if not knowledge.get("meta", {}).get("skipped"):
            pct = knowledge.get("pct", 0)
            if pct < self.thresholds["knowledge"]:
                alerts.append({
                    "severity": "warning",
                    "benchmark": "knowledge",
                    "message": f"Knowledge accuracy dropped to {pct}% (threshold: {self.thresholds['knowledge']}%)",
                })

        # Hallucination rate
        hallucination = benchmarks.get("hallucination", {})
        if not hallucination.get("meta", {}).get("skipped"):
            pct = hallucination.get("pct", 0)
            if pct < self.thresholds["hallucination"]:
                h_rate = hallucination.get("meta", {}).get("hallucination_rate", "?")
                alerts.append({
                    "severity": "warning",
                    "benchmark": "hallucination",
                    "message": f"Hallucination rate at {h_rate}% - uncertainty admission only {pct}% (threshold: {self.thresholds['hallucination']}%)",
                })

        # Latency
        latency = benchmarks.get("latency", {})
        if not latency.get("meta", {}).get("skipped"):
            p50 = latency.get("meta", {}).get("p50", 0)
            p95 = latency.get("meta", {}).get("p95", 0)
            if p50 > self.thresholds["latency_p50_max"]:
                alerts.append({
                    "severity": "critical" if p50 > self.thresholds["latency_p50_max"] * 2 else "warning",
                    "benchmark": "latency",
                    "message": f"Response p50 latency {p50:.1f}s exceeds {self.thresholds['latency_p50_max']}s threshold",
                })
            if p95 > self.thresholds["latency_p95_max"]:
                alerts.append({
                    "severity": "critical",
                    "benchmark": "latency",
                    "message": f"Response p95 latency {p95:.1f}s exceeds {self.thresholds['latency_p95_max']}s threshold",
                })

        # Overall composite
        overall = report.get("summary", {}).get("overall", {})
        composite = overall.get("composite_score", 0)
        if composite < self.thresholds["overall"]:
            alerts.append({
                "severity": "critical",
                "benchmark": "overall",
                "message": f"Overall quality score {composite}% below threshold {self.thresholds['overall']}%",
            })

        # Record alerts
        for alert in alerts:
            alert["timestamp"] = datetime.now(timezone.utc).isoformat()
            self.alert_history.append(alert)

        return alerts

    def dispatch_alerts(self, alerts: List[Dict[str, str]]) -> None:
        """Send alerts via available channels."""
        if not alerts:
            return

        for alert in alerts:
            severity = alert["severity"].upper()
            msg = f"[{severity}] Bruce Quality Alert: {alert['message']}"
            logger.warning(msg)

            # Try Telegram
            if TELEGRAM_AVAILABLE:
                try:
                    send_alert(msg)
                except Exception as e:
                    logger.debug(f"Telegram alert failed: {e}")

            # Console always
            print(f"  ALERT [{severity}] {alert['message']}")


# ============================================================================
# Quality Monitor
# ============================================================================

class QualityMonitor:
    """
    Periodic quality monitoring for Bruce AI.

    Usage:
        monitor = QualityMonitor()
        monitor.run_check()           # single check
        monitor.run_daemon(hours=6)   # continuous monitoring
        monitor.get_trend_report()    # historical analysis
    """

    def __init__(self, llm=None, thresholds: Optional[Dict[str, float]] = None,
                 n_questions: int = 10):
        self.llm = llm
        self.n_questions = n_questions
        self.alert_manager = AlertManager(thresholds)
        self._running = False

        if not self.llm and LLM_AVAILABLE:
            try:
                self.llm = LLMBridge(provider="local")
            except Exception:
                pass

    def run_check(self) -> Dict[str, Any]:
        """Run a single quality check and return results."""
        if not BENCHMARK_AVAILABLE:
            logger.error("Benchmark module not available")
            return {"error": "Benchmark module not available"}

        logger.info(f"Running quality check ({self.n_questions} questions)...")
        suite = BenchmarkSuite(llm=self.llm, auto_init_llm=False)
        suite.run_quick(n_questions=self.n_questions)
        report = suite.get_report()

        # Check thresholds and dispatch alerts
        alerts = self.alert_manager.check(report)
        self.alert_manager.dispatch_alerts(alerts)

        # Build trend entry
        trend_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scores": {},
            "alerts_count": len(alerts),
        }
        for name, bdata in report.get("benchmarks", {}).items():
            if not bdata.get("meta", {}).get("skipped"):
                trend_entry["scores"][name] = bdata.get("pct", 0)

        overall = report.get("summary", {}).get("overall", {})
        trend_entry["scores"]["overall"] = overall.get("composite_score", 0)

        # Save trend
        append_trend(trend_entry)

        # Also save full report
        suite.save_report(report)

        logger.info(f"Quality check complete. Composite: {overall.get('composite_score', 0)}%")
        if alerts:
            logger.warning(f"  {len(alerts)} alert(s) triggered!")

        return {
            "report": report,
            "alerts": alerts,
            "trend_entry": trend_entry,
        }

    def run_daemon(self, hours: float = 6.0) -> None:
        """Run continuously, checking every N hours."""
        interval = hours * 3600
        self._running = True

        # Handle graceful shutdown
        def _shutdown(signum, frame):
            logger.info("Shutting down quality monitor...")
            self._running = False

        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)

        logger.info(f"Quality monitor daemon started (interval: {hours}h)")
        print(f"[*] Quality Monitor running every {hours} hours. Press Ctrl+C to stop.")

        while self._running:
            try:
                result = self.run_check()
                composite = result.get("report", {}).get(
                    "summary", {}
                ).get("overall", {}).get("composite_score", 0)
                alert_count = len(result.get("alerts", []))
                print(f"  [{datetime.now().strftime('%Y-%m-%d %H:%M')}] "
                      f"Score: {composite}% | Alerts: {alert_count}")
            except Exception as e:
                logger.error(f"Quality check failed: {e}")
                print(f"  [ERROR] Quality check failed: {e}")

            # Sleep in small increments so we can respond to shutdown signals
            end_time = time.time() + interval
            while self._running and time.time() < end_time:
                time.sleep(min(30, end_time - time.time()))

        logger.info("Quality monitor stopped.")

    def get_trend_report(self, last_n: int = 50) -> Dict[str, Any]:
        """Analyze quality trends from historical data."""
        trends = load_trends()
        if not trends:
            return {"error": "No trend data available. Run some checks first."}

        recent = trends[-last_n:]

        report = {
            "total_checks": len(trends),
            "analyzed": len(recent),
            "period": {
                "from": recent[0]["timestamp"] if recent else None,
                "to": recent[-1]["timestamp"] if recent else None,
            },
            "metrics": {},
            "alerts_total": sum(e.get("alerts_count", 0) for e in recent),
        }

        # Aggregate scores per metric
        metric_values: Dict[str, List[float]] = {}
        for entry in recent:
            for metric, value in entry.get("scores", {}).items():
                metric_values.setdefault(metric, []).append(value)

        for metric, values in metric_values.items():
            if not values:
                continue

            n = len(values)
            current = values[-1]
            first = values[0]

            report["metrics"][metric] = {
                "current": current,
                "mean": round(statistics.mean(values), 2),
                "min": round(min(values), 2),
                "max": round(max(values), 2),
                "stdev": round(statistics.stdev(values), 2) if n > 1 else 0,
                "trend": round(current - first, 2),
                "trend_direction": "improving" if current > first else "declining" if current < first else "stable",
                "data_points": n,
            }

        return report

    def print_trend_report(self) -> None:
        """Print a formatted trend report to stdout."""
        report = self.get_trend_report()

        if "error" in report:
            print(f"\n[!] {report['error']}\n")
            return

        print()
        print("=" * 65)
        print("  BRUCE AI - QUALITY TREND REPORT")
        print("=" * 65)
        print(f"  Total checks: {report['total_checks']}")
        print(f"  Period: {report['period']['from']}")
        print(f"       to {report['period']['to']}")
        print(f"  Total alerts: {report['alerts_total']}")
        print()
        print(f"  {'Metric':<20} {'Current':>8} {'Mean':>8} {'Min':>8} {'Max':>8} {'Trend':>10}")
        print(f"  {'-'*20} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*10}")

        for metric, data in report.get("metrics", {}).items():
            trend_val = data["trend"]
            trend_sym = "+" if trend_val > 0 else ""
            direction = data["trend_direction"]
            marker = "^" if direction == "improving" else "v" if direction == "declining" else "="

            print(f"  {metric:<20} {data['current']:>7.1f}% {data['mean']:>7.1f}% "
                  f"{data['min']:>7.1f}% {data['max']:>7.1f}% "
                  f"{trend_sym}{trend_val:>6.1f}% {marker}")

        print()
        print("  ^ = improving  v = declining  = = stable")
        print("=" * 65)
        print()


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Bruce AI Quality Monitor")
    parser.add_argument("--daemon", action="store_true", help="Run continuously in background")
    parser.add_argument("--interval", type=float, default=6.0, help="Hours between checks (default: 6)")
    parser.add_argument("--questions", type=int, default=10, help="Number of questions per check (default: 10)")
    parser.add_argument("--report", action="store_true", help="Show trend report")
    parser.add_argument("--provider", type=str, default="local", help="LLM provider")
    parser.add_argument("--threshold-knowledge", type=float, default=None)
    parser.add_argument("--threshold-hallucination", type=float, default=None)
    parser.add_argument("--threshold-overall", type=float, default=None)

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

    # Build custom thresholds
    thresholds = DEFAULT_THRESHOLDS.copy()
    if args.threshold_knowledge is not None:
        thresholds["knowledge"] = args.threshold_knowledge
    if args.threshold_hallucination is not None:
        thresholds["hallucination"] = args.threshold_hallucination
    if args.threshold_overall is not None:
        thresholds["overall"] = args.threshold_overall

    # Initialize LLM
    llm = None
    if LLM_AVAILABLE:
        try:
            llm = LLMBridge(provider=args.provider)
            print(f"[*] LLM initialized: {args.provider}")
        except Exception as e:
            print(f"[!] Could not initialize LLM: {e}")

    monitor = QualityMonitor(llm=llm, thresholds=thresholds, n_questions=args.questions)

    if args.report:
        monitor.print_trend_report()
    elif args.daemon:
        monitor.run_daemon(hours=args.interval)
    else:
        print("\n[*] Running single quality check...\n")
        result = monitor.run_check()
        report = result.get("report", {})
        overall = report.get("summary", {}).get("overall", {})
        print(f"\n[*] Composite score: {overall.get('composite_score', 0)}%")
        alerts = result.get("alerts", [])
        if alerts:
            print(f"[!] {len(alerts)} alert(s):")
            for a in alerts:
                print(f"    [{a['severity'].upper()}] {a['message']}")
        print()


if __name__ == "__main__":
    main()
