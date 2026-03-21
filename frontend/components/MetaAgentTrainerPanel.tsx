import React, { useState, useEffect, useCallback } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface Agent {
  id: string;
  name: string;
  status: "idle" | "training" | "ready" | "error";
  accuracy: number;
}

interface TrainingConfig {
  epochs: number;
  learningRate: number;
  batchSize: number;
}

interface LossPoint {
  epoch: number;
  loss: number;
}

export default function MetaAgentTrainerPanel() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [config, setConfig] = useState<TrainingConfig>({ epochs: 10, learningRate: 0.001, batchSize: 32 });
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [training, setTraining] = useState(false);
  const [progress, setProgress] = useState(0);
  const [lossData, setLossData] = useState<LossPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAgents = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/agents`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setAgents(data.agents || [
        { id: "agent-1", name: "Market Analyst", status: "ready", accuracy: 0.87 },
        { id: "agent-2", name: "Risk Manager", status: "idle", accuracy: 0.72 },
        { id: "agent-3", name: "Sentiment Tracker", status: "idle", accuracy: 0.65 },
      ]);
      setError(null);
    } catch {
      setAgents([
        { id: "agent-1", name: "Market Analyst", status: "ready", accuracy: 0.87 },
        { id: "agent-2", name: "Risk Manager", status: "idle", accuracy: 0.72 },
        { id: "agent-3", name: "Sentiment Tracker", status: "idle", accuracy: 0.65 },
      ]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAgents(); }, [fetchAgents]);

  const startTraining = async () => {
    if (!selectedAgent) return;
    setTraining(true);
    setProgress(0);
    setLossData([]);

    try {
      await fetch(`${API_URL}/api/v1/training/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agentId: selectedAgent, ...config }),
      });
    } catch { /* continue with simulation */ }

    // Simulate progress
    for (let i = 1; i <= config.epochs; i++) {
      await new Promise((r) => setTimeout(r, 400));
      setProgress((i / config.epochs) * 100);
      setLossData((prev) => [...prev, { epoch: i, loss: 2.5 * Math.exp(-0.3 * i) + Math.random() * 0.1 }]);
    }

    setAgents((prev) =>
      prev.map((a) => (a.id === selectedAgent ? { ...a, status: "ready" as const, accuracy: Math.min(a.accuracy + 0.05, 0.99) } : a))
    );
    setTraining(false);
  };

  const STATUS_COLORS: Record<string, string> = {
    idle: "text-gray-400",
    training: "text-yellow-400",
    ready: "text-green-400",
    error: "text-red-400",
  };

  if (loading) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 animate-pulse space-y-3">
        <div className="h-4 bg-gray-700 rounded w-1/3" />
        <div className="h-32 bg-gray-800 rounded" />
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-5">
      <h2 className="text-lg font-bold text-amber-300">Meta-Agent Trainer</h2>

      {/* Agent List */}
      <div className="space-y-2">
        {agents.map((agent) => (
          <div
            key={agent.id}
            onClick={() => !training && setSelectedAgent(agent.id)}
            className={`flex items-center justify-between p-3 rounded-lg cursor-pointer border transition-colors ${
              selectedAgent === agent.id ? "border-amber-600 bg-amber-900/20" : "border-gray-700 bg-gray-800 hover:bg-gray-750"
            }`}
          >
            <div>
              <span className="text-sm text-gray-200">{agent.name}</span>
              <span className={`ml-2 text-xs ${STATUS_COLORS[agent.status]}`}>{agent.status.toUpperCase()}</span>
            </div>
            <span className="text-xs text-gray-400">Acc: {(agent.accuracy * 100).toFixed(1)}%</span>
          </div>
        ))}
      </div>

      {/* Config */}
      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="text-xs text-gray-400 block mb-1">Epochs</label>
          <input
            type="number" min={1} max={100} value={config.epochs}
            onChange={(e) => setConfig({ ...config, epochs: Number(e.target.value) })}
            disabled={training}
            className="w-full bg-gray-800 border border-gray-600 text-gray-200 text-sm rounded px-2 py-1.5 focus:border-amber-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="text-xs text-gray-400 block mb-1">Learning Rate</label>
          <input
            type="number" step={0.0001} min={0.0001} max={1} value={config.learningRate}
            onChange={(e) => setConfig({ ...config, learningRate: Number(e.target.value) })}
            disabled={training}
            className="w-full bg-gray-800 border border-gray-600 text-gray-200 text-sm rounded px-2 py-1.5 focus:border-amber-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="text-xs text-gray-400 block mb-1">Batch Size</label>
          <input
            type="number" min={1} max={512} value={config.batchSize}
            onChange={(e) => setConfig({ ...config, batchSize: Number(e.target.value) })}
            disabled={training}
            className="w-full bg-gray-800 border border-gray-600 text-gray-200 text-sm rounded px-2 py-1.5 focus:border-amber-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Progress Bar */}
      {training && (
        <div>
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            <span>Training Progress</span>
            <span>{progress.toFixed(0)}%</span>
          </div>
          <div className="w-full h-3 bg-gray-700 rounded overflow-hidden">
            <div className="h-full bg-amber-500 rounded transition-all" style={{ width: `${progress}%` }} />
          </div>
        </div>
      )}

      {/* Loss Chart */}
      {lossData.length > 0 && (
        <div className="w-full h-40">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={lossData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="epoch" tick={{ fill: "#9ca3af", fontSize: 10 }} />
              <YAxis tick={{ fill: "#9ca3af", fontSize: 10 }} />
              <Tooltip contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #374151", borderRadius: 8 }} />
              <Line type="monotone" dataKey="loss" stroke="#f59e0b" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <button
        onClick={startTraining}
        disabled={!selectedAgent || training}
        className="w-full px-4 py-2 bg-amber-700 hover:bg-amber-600 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm rounded-lg transition-colors"
      >
        {training ? "Training..." : "Start Training"}
      </button>
    </div>
  );
}
