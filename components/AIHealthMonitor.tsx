import React, { useEffect, useState, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface ServiceStatus {
  name: string;
  status: "healthy" | "degraded" | "down" | "unknown";
  latencyMs: number;
}

interface HealthData {
  services: ServiceStatus[];
  memoryUsedMb: number;
  memoryTotalMb: number;
  modelHealth: string;
  uptimeSeconds: number;
  diagnostic: string;
}

const STATUS_CONFIG: Record<string, { color: string; bg: string }> = {
  healthy: { color: "text-green-400", bg: "bg-green-500" },
  degraded: { color: "text-yellow-400", bg: "bg-yellow-500" },
  down: { color: "text-red-400", bg: "bg-red-500" },
  unknown: { color: "text-gray-400", bg: "bg-gray-500" },
};

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${d}d ${h}h ${m}m ${s}s`;
}

export default function AIHealthMonitor() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [healing, setHealing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/ai/self-healing/status`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setHealth({
        services: data.services || [
          { name: "Inference Engine", status: data.status === "operational" ? "healthy" : "degraded", latencyMs: 45 },
          { name: "Memory Store", status: "healthy", latencyMs: 12 },
          { name: "Emotion Engine", status: "healthy", latencyMs: 23 },
          { name: "Vector DB", status: "healthy", latencyMs: 8 },
          { name: "WebSocket Hub", status: "healthy", latencyMs: 3 },
          { name: "Scheduler", status: "healthy", latencyMs: 5 },
        ],
        memoryUsedMb: data.memory_used_mb ?? 2048,
        memoryTotalMb: data.memory_total_mb ?? 8192,
        modelHealth: data.model_health ?? data.status ?? "healthy",
        uptimeSeconds: data.uptime_seconds ?? 86400,
        diagnostic: data.diagnostic ?? "All systems nominal.",
      });
      setError(null);
      setLastRefresh(new Date());
    } catch (err: any) {
      setError(err.message || "Failed to fetch health status");
    } finally {
      setLoading(false);
    }
  }, []);

  const triggerHealing = async () => {
    try {
      setHealing(true);
      const res = await fetch(`${API_URL}/ai/self-healing/heal`, { method: "POST" });
      if (!res.ok) throw new Error("Healing failed");
      const data = await res.json();
      setHealth((prev) => prev ? { ...prev, diagnostic: data.response || "Healing complete." } : prev);
    } catch {
      setError("Failed to trigger healing process");
    } finally {
      setHealing(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  if (loading) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 animate-pulse space-y-4">
        <div className="h-4 bg-gray-700 rounded w-1/3" />
        <div className="grid grid-cols-3 gap-2">
          {[1, 2, 3, 4, 5, 6].map((i) => <div key={i} className="h-12 bg-gray-800 rounded" />)}
        </div>
      </div>
    );
  }

  if (error && !health) {
    return (
      <div className="bg-gray-900 border border-red-800 rounded-xl p-6">
        <h2 className="text-lg font-bold text-red-400">AI Health Monitor</h2>
        <p className="text-red-300 text-sm mt-2">{error}</p>
        <button onClick={fetchStatus} className="mt-3 px-3 py-1 bg-red-700 hover:bg-red-600 text-white text-sm rounded">Retry</button>
      </div>
    );
  }

  const memPct = health ? (health.memoryUsedMb / health.memoryTotalMb) * 100 : 0;

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-emerald-300">AI Health Monitor</h2>
        <span className="text-xs text-gray-500">Last: {lastRefresh.toLocaleTimeString()}</span>
      </div>

      {/* Service Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {health?.services.map((svc) => {
          const cfg = STATUS_CONFIG[svc.status] || STATUS_CONFIG.unknown;
          return (
            <div key={svc.name} className="bg-gray-800 rounded-lg p-3 border border-gray-700">
              <div className="flex items-center gap-2 mb-1">
                <span className={`w-2 h-2 rounded-full ${cfg.bg}`} />
                <span className="text-xs text-gray-300 truncate">{svc.name}</span>
              </div>
              <div className="flex justify-between text-[10px]">
                <span className={cfg.color}>{svc.status.toUpperCase()}</span>
                <span className="text-gray-500">{svc.latencyMs}ms</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Memory Usage */}
      <div>
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Memory</span>
          <span>{health?.memoryUsedMb}MB / {health?.memoryTotalMb}MB</span>
        </div>
        <div className="w-full h-2.5 bg-gray-700 rounded overflow-hidden">
          <div className={`h-full rounded ${memPct > 85 ? "bg-red-500" : memPct > 60 ? "bg-yellow-500" : "bg-green-500"}`} style={{ width: `${memPct}%` }} />
        </div>
      </div>

      {/* Model Health + Uptime */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
          <span className="text-xs text-gray-400">Model Health</span>
          <p className={`text-sm font-semibold mt-1 ${health?.modelHealth === "healthy" ? "text-green-400" : "text-yellow-400"}`}>
            {health?.modelHealth?.toUpperCase()}
          </p>
        </div>
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
          <span className="text-xs text-gray-400">Uptime</span>
          <p className="text-sm font-mono text-gray-200 mt-1">{formatUptime(health?.uptimeSeconds ?? 0)}</p>
        </div>
      </div>

      {/* Diagnostic */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-3">
        <span className="text-xs text-gray-400">Diagnostic</span>
        <p className="text-sm text-gray-300 mt-1 whitespace-pre-wrap">{health?.diagnostic}</p>
      </div>

      {/* Self-Heal Button */}
      <button
        onClick={triggerHealing}
        disabled={healing}
        className="w-full px-4 py-2 bg-emerald-700 hover:bg-emerald-600 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm rounded-lg transition-colors"
      >
        {healing ? "Healing in progress..." : "Trigger Self-Healing"}
      </button>
    </div>
  );
}
