import React, { useEffect, useState, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import Badge from "@/components/ui/badge";
import Progress from "@/components/ui/progress";
import { motion } from "framer-motion";

interface CognitiveStatus {
  overallHealth: number;
  modules: {
    name: string;
    status: "active" | "idle" | "error" | "healing";
    health: number;
    lastActivity: string;
  }[];
  predictions: {
    label: string;
    confidence: number;
    direction: "up" | "down" | "neutral";
  }[];
  rewardHistory: number[];
  episodeCount: number;
  uptime: number;
}

const CognitiveDashboard = () => {
  const [status, setStatus] = useState<CognitiveStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch("/internal/ai/status");
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch {
      // Use default data
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  // Default mock data
  const modules = status?.modules || [
    { name: "Memory Core", status: "active" as const, health: 97, lastActivity: "2s ago" },
    { name: "Emotion Engine", status: "active" as const, health: 91, lastActivity: "5s ago" },
    { name: "Strategy Mind", status: "active" as const, health: 88, lastActivity: "12s ago" },
    { name: "TIA Agent", status: "idle" as const, health: 100, lastActivity: "1m ago" },
    { name: "Self-Healing", status: "active" as const, health: 95, lastActivity: "30s ago" },
    { name: "RL Trainer", status: "idle" as const, health: 82, lastActivity: "5m ago" },
  ];

  const predictions = status?.predictions || [
    { label: "BTC Short-term", confidence: 0.78, direction: "up" as const },
    { label: "ETH Momentum", confidence: 0.65, direction: "neutral" as const },
    { label: "Market Volatility", confidence: 0.82, direction: "up" as const },
  ];

  const overallHealth = status?.overallHealth ?? 92;

  const statusVariant = (s: string) => {
    const map: Record<string, "success" | "info" | "error" | "warning"> = {
      active: "success", idle: "info", error: "error", healing: "warning",
    };
    return map[s] || "neutral";
  };

  const directionSymbol = (d: string) => {
    if (d === "up") return { symbol: "\u2191", color: "text-emerald-400" };
    if (d === "down") return { symbol: "\u2193", color: "text-red-400" };
    return { symbol: "\u2192", color: "text-zinc-400" };
  };

  return (
    <motion.div
      className="space-y-4"
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <Card className="bg-zinc-900 border-zinc-800">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Cognitive Dashboard</h2>
            <div className="flex items-center gap-2">
              <Badge variant={overallHealth > 80 ? "success" : "warning"} dot>
                Health: {overallHealth}%
              </Badge>
            </div>
          </div>

          {/* Summary Stats */}
          <div className="grid grid-cols-4 gap-3 mb-4">
            <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
              <p className="text-xs text-zinc-400">Overall Health</p>
              <p className="text-xl font-bold text-emerald-400">{overallHealth}%</p>
            </div>
            <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
              <p className="text-xs text-zinc-400">Active Modules</p>
              <p className="text-xl font-bold text-indigo-400">
                {modules.filter(m => m.status === "active").length}/{modules.length}
              </p>
            </div>
            <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
              <p className="text-xs text-zinc-400">Episodes</p>
              <p className="text-xl font-bold text-blue-400">{status?.episodeCount ?? 1247}</p>
            </div>
            <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
              <p className="text-xs text-zinc-400">Uptime</p>
              <p className="text-xl font-bold text-amber-400">
                {status?.uptime ? `${(status.uptime / 3600).toFixed(1)}h` : "99.7%"}
              </p>
            </div>
          </div>

          {/* Modules Grid */}
          <h3 className="text-sm font-medium text-zinc-400 mb-2">System Modules</h3>
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-2 mb-4">
            {modules.map((mod) => (
              <div key={mod.name} className="bg-zinc-800/30 rounded-lg p-3 border border-zinc-700/30">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-sm font-medium text-zinc-200">{mod.name}</span>
                  <Badge variant={statusVariant(mod.status)} size="sm">{mod.status}</Badge>
                </div>
                <Progress
                  value={mod.health}
                  variant={mod.health >= 90 ? "success" : mod.health >= 70 ? "warning" : "error"}
                  size="sm"
                />
                <p className="text-xs text-zinc-600 mt-1">{mod.lastActivity}</p>
              </div>
            ))}
          </div>

          {/* Predictions */}
          <h3 className="text-sm font-medium text-zinc-400 mb-2">Active Predictions</h3>
          <div className="space-y-2">
            {predictions.map((pred, idx) => {
              const dir = directionSymbol(pred.direction);
              return (
                <div key={idx} className="flex items-center gap-3 p-2 rounded-lg bg-zinc-800/30">
                  <span className={`text-lg font-bold ${dir.color}`}>{dir.symbol}</span>
                  <span className="text-sm text-zinc-300 flex-1">{pred.label}</span>
                  <div className="flex items-center gap-2">
                    <Progress
                      value={pred.confidence * 100}
                      variant={pred.confidence >= 0.7 ? "success" : "warning"}
                      size="sm"
                      className="w-20"
                    />
                    <span className="text-xs font-mono text-zinc-400">
                      {(pred.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default CognitiveDashboard;
