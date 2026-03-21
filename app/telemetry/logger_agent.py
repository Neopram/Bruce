# Advanced telemetry logger for behaviors
import time
import threading
from collections import defaultdict


class TelemetryAgent:
    """Telemetry logging agent for events, metrics, and system health monitoring."""

    def __init__(self, buffer_size=100):
        self._events = []
        self._metrics = defaultdict(list)
        self._buffer = []
        self._buffer_size = buffer_size
        self._lock = threading.Lock()
        self._start_time = time.time()

    def log_event(self, event_type, data=None):
        """Log a telemetry event.

        Args:
            event_type: Category string (e.g., 'trade_executed', 'user_login', 'error').
            data: Optional dict with event details.

        Returns:
            Dict confirming the event was logged.
        """
        event = {
            "event_type": event_type,
            "data": data or {},
            "timestamp": time.time(),
        }
        with self._lock:
            self._buffer.append(event)
            if len(self._buffer) >= self._buffer_size:
                self._flush_buffer()
        return {"status": "logged", "event_type": event_type}

    def log_metric(self, name, value, tags=None):
        """Log a numeric metric with optional tags.

        Args:
            name: Metric name (e.g., 'latency_ms', 'portfolio_value', 'cpu_usage').
            value: Numeric value.
            tags: Optional dict of key-value tags for filtering.

        Returns:
            Dict confirming the metric was logged.
        """
        metric = {
            "name": name,
            "value": value,
            "tags": tags or {},
            "timestamp": time.time(),
        }
        with self._lock:
            self._metrics[name].append(metric)
        return {"status": "logged", "metric": name, "value": value}

    def get_metrics(self, name, period=None):
        """Retrieve metrics by name, optionally filtered by time period.

        Args:
            name: Metric name to retrieve.
            period: Optional time window in seconds (e.g., 3600 for last hour).

        Returns:
            Dict with metric values and summary statistics.
        """
        with self._lock:
            all_metrics = list(self._metrics.get(name, []))

        if period:
            cutoff = time.time() - period
            all_metrics = [m for m in all_metrics if m["timestamp"] >= cutoff]

        if not all_metrics:
            return {"name": name, "count": 0, "values": []}

        values = [m["value"] for m in all_metrics]
        avg = sum(values) / len(values)
        min_val = min(values)
        max_val = max(values)

        return {
            "name": name,
            "count": len(values),
            "average": round(avg, 4),
            "min": round(min_val, 4),
            "max": round(max_val, 4),
            "latest": round(values[-1], 4),
            "values": [{"value": round(m["value"], 4), "timestamp": m["timestamp"]} for m in all_metrics[-50:]],
        }

    def get_system_health(self):
        """Generate an overall system health report from collected telemetry.

        Returns:
            Dict with uptime, event counts, metric summaries, and health status.
        """
        uptime = time.time() - self._start_time

        with self._lock:
            total_events = len(self._events) + len(self._buffer)
            event_types = defaultdict(int)
            for e in self._events + self._buffer:
                event_types[e["event_type"]] += 1

            metric_names = list(self._metrics.keys())
            metric_summaries = {}
            for name in metric_names:
                vals = [m["value"] for m in self._metrics[name]]
                if vals:
                    metric_summaries[name] = {
                        "count": len(vals),
                        "average": round(sum(vals) / len(vals), 4),
                        "latest": round(vals[-1], 4),
                    }

        # Determine health status
        error_count = event_types.get("error", 0)
        if error_count > 10:
            health = "critical"
        elif error_count > 3:
            health = "degraded"
        else:
            health = "healthy"

        return {
            "health": health,
            "uptime_seconds": round(uptime, 2),
            "total_events": total_events,
            "event_types": dict(event_types),
            "metric_summaries": metric_summaries,
            "buffer_usage": f"{len(self._buffer)}/{self._buffer_size}",
        }

    def flush(self):
        """Flush all pending events from the buffer to permanent storage.

        Returns:
            Dict with count of flushed events.
        """
        with self._lock:
            count = self._flush_buffer()
        return {"status": "flushed", "events_flushed": count}

    def _flush_buffer(self):
        """Internal: move buffer contents to events list. Must be called with lock held."""
        count = len(self._buffer)
        self._events.extend(self._buffer)
        self._buffer = []
        return count

    def get_events(self, event_type=None, limit=50):
        """Retrieve logged events, optionally filtered by type.

        Args:
            event_type: Optional filter for event type.
            limit: Max events to return (default 50).
        """
        with self._lock:
            all_events = self._events + self._buffer

        if event_type:
            all_events = [e for e in all_events if e["event_type"] == event_type]

        return all_events[-limit:]

    def clear(self):
        """Clear all telemetry data."""
        with self._lock:
            self._events.clear()
            self._buffer.clear()
            self._metrics.clear()
        return {"status": "cleared"}
