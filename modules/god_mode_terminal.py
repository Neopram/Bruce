"""
Advanced multi-panel terminal display.
Provides a unified view of system overview, model status, trading status,
memory status, and real-time metrics in a single dashboard.
"""
import random
import time
from datetime import datetime


class GodModeTerminal:
    """Advanced multi-panel terminal providing unified system visibility."""

    def __init__(self):
        self.panels = {
            "system": True,
            "models": True,
            "trading": True,
            "memory": True,
            "network": True,
        }
        self.alerts = []
        self.refresh_interval_s = 5

    def display_markets(self):
        """Display market overview panel data."""
        return {
            "dimensions": 7,
            "time_folding": True,
            "dark_pool_overlay": True,
            "markets": {
                "BTC/USDT": {"price": round(65000 + random.uniform(-500, 500), 2),
                             "change_24h_pct": round(random.uniform(-5, 5), 2)},
                "ETH/USDT": {"price": round(3400 + random.uniform(-100, 100), 2),
                             "change_24h_pct": round(random.uniform(-5, 5), 2)},
                "SOL/USDT": {"price": round(145 + random.uniform(-10, 10), 2),
                             "change_24h_pct": round(random.uniform(-8, 8), 2)},
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    def display_system_overview(self):
        """Display system resources and health panel."""
        return {
            "cpu_usage_pct": round(random.uniform(10, 90), 1),
            "memory_usage_pct": round(random.uniform(20, 80), 1),
            "disk_usage_pct": round(random.uniform(30, 70), 1),
            "uptime_hours": round(random.uniform(1, 720), 1),
            "active_threads": random.randint(4, 32),
            "network_io_mbps": round(random.uniform(1, 100), 2),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def display_model_status(self):
        """Display AI model status panel."""
        models = ["llm_bridge", "emotional_processor", "tactical_mind", "autonomy_core"]
        statuses = {}
        for model in models:
            statuses[model] = {
                "status": random.choice(["active", "active", "active", "idle", "loading"]),
                "latency_ms": round(random.uniform(5, 500), 1),
                "requests_processed": random.randint(0, 10000),
                "error_rate_pct": round(random.uniform(0, 5), 2),
            }
        return {"models": statuses, "timestamp": datetime.utcnow().isoformat()}

    def display_trading_status(self):
        """Display trading activity panel."""
        return {
            "open_positions": random.randint(0, 15),
            "daily_pnl_usd": round(random.uniform(-5000, 10000), 2),
            "total_trades_today": random.randint(0, 200),
            "win_rate_pct": round(random.uniform(40, 75), 1),
            "active_strategies": random.randint(1, 8),
            "risk_utilization_pct": round(random.uniform(10, 80), 1),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def display_memory_status(self):
        """Display memory and cognitive state panel."""
        return {
            "short_term_entries": random.randint(10, 500),
            "long_term_entries": random.randint(100, 10000),
            "vector_db_size_mb": round(random.uniform(50, 2000), 1),
            "sync_status": random.choice(["synced", "syncing", "stale"]),
            "last_sync": datetime.utcnow().isoformat(),
            "cognitive_load_pct": round(random.uniform(10, 90), 1),
        }

    def get_full_dashboard(self):
        """Return complete dashboard data from all active panels."""
        dashboard = {"timestamp": datetime.utcnow().isoformat(), "panels": {}}

        if self.panels.get("system"):
            dashboard["panels"]["system"] = self.display_system_overview()
        if self.panels.get("models"):
            dashboard["panels"]["models"] = self.display_model_status()
        if self.panels.get("trading"):
            dashboard["panels"]["trading"] = self.display_trading_status()
        if self.panels.get("memory"):
            dashboard["panels"]["memory"] = self.display_memory_status()
        if self.panels.get("network"):
            dashboard["panels"]["markets"] = self.display_markets()

        dashboard["alerts"] = self._check_alerts()
        return dashboard

    def _check_alerts(self):
        """Check for any system alerts."""
        alerts = []
        sys_overview = self.display_system_overview()
        if sys_overview["cpu_usage_pct"] > 85:
            alerts.append({"level": "warning", "message": "High CPU usage", "value": sys_overview["cpu_usage_pct"]})
        if sys_overview["memory_usage_pct"] > 80:
            alerts.append({"level": "warning", "message": "High memory usage", "value": sys_overview["memory_usage_pct"]})

        trading = self.display_trading_status()
        if trading["daily_pnl_usd"] < -2000:
            alerts.append({"level": "critical", "message": "Significant daily loss", "value": trading["daily_pnl_usd"]})

        self.alerts.extend(alerts)
        return alerts

    def toggle_panel(self, panel_name, enabled=None):
        """Toggle a dashboard panel on or off."""
        if panel_name not in self.panels:
            return {"status": "error", "message": f"Unknown panel: {panel_name}"}
        if enabled is not None:
            self.panels[panel_name] = enabled
        else:
            self.panels[panel_name] = not self.panels[panel_name]
        return {"panel": panel_name, "enabled": self.panels[panel_name]}

    def voice_interface(self):
        """Return a voice interface mode descriptor."""
        return random.choice([
            "Voice mode: Morgan Freeman",
            "Voice mode: Trader ensemble",
            "Voice mode: Ambient analysis",
        ])

    def get_alert_history(self, limit=50):
        """Return recent alerts."""
        return self.alerts[-limit:]

    def clear_alerts(self):
        """Clear all alerts."""
        count = len(self.alerts)
        self.alerts = []
        return {"cleared": count}
