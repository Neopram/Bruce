import React, { useEffect, useState, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface CognitiveState {
  memoryCount: number;
  activePersonality: string;
  loadedModels: string[];
  recentDecisions: number;
  lastThought: string;
  mood: string;
  nextIntent: string;
  cognitiveLoad: number;
}

export default function CognitiveStatusPanel() {
  const [state, setState] = useState<CognitiveState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/bruce-api/cognition/status`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setState({
        memoryCount: data.memory_count ?? data.memoryCount ?? 0,
        activePersonality: data.active_personality ?? data.personality ?? "Default",
        loadedModels: data.loaded_models ?? data.models ?? [],
        recentDecisions: data.recent_decisions ?? data.decisions ?? 0,
        lastThought: data.last_thought ?? "No recent thoughts",
        mood: data.mood ?? "Neutral",
        nextIntent: data.next_intent ?? "Awaiting input",
        cognitiveLoad: data.cognitive_load ?? 0.4,
      });
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to fetch cognitive status");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 8000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  if (loading) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 animate-pulse space-y-3">
        <div className="h-4 bg-gray-700 rounded w-1/3" />
        {[1, 2, 3, 4].map((i) => <div key={i} className="h-8 bg-gray-800 rounded" />)}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-900 border border-red-800 rounded-xl p-6">
        <h2 className="text-lg font-bold text-red-400">Cognitive Status</h2>
        <p className="text-red-300 text-sm mt-2">{error}</p>
        <button onClick={fetchStatus} className="mt-3 px-3 py-1 bg-red-700 hover:bg-red-600 text-white text-sm rounded">Retry</button>
      </div>
    );
  }

  const loadPct = (state?.cognitiveLoad ?? 0) * 100;

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-4">
      <h2 className="text-lg font-bold text-violet-300">Cognitive Status</h2>

      <div className="grid grid-cols-2 gap-3">
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
          <span className="text-xs text-gray-400">Memories</span>
          <p className="text-xl font-bold text-violet-300">{state?.memoryCount}</p>
        </div>
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
          <span className="text-xs text-gray-400">Recent Decisions</span>
          <p className="text-xl font-bold text-cyan-300">{state?.recentDecisions}</p>
        </div>
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
          <span className="text-xs text-gray-400">Active Personality</span>
          <p className="text-sm font-semibold text-amber-300 mt-1">{state?.activePersonality}</p>
        </div>
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
          <span className="text-xs text-gray-400">Mood</span>
          <p className="text-sm font-semibold text-pink-300 mt-1">{state?.mood}</p>
        </div>
      </div>

      {/* Cognitive Load Bar */}
      <div>
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Cognitive Load</span>
          <span>{loadPct.toFixed(0)}%</span>
        </div>
        <div className="w-full h-2.5 bg-gray-700 rounded overflow-hidden">
          <div
            className={`h-full rounded transition-all ${loadPct > 80 ? "bg-red-500" : loadPct > 50 ? "bg-yellow-500" : "bg-green-500"}`}
            style={{ width: `${loadPct}%` }}
          />
        </div>
      </div>

      {/* Loaded Models */}
      <div>
        <span className="text-xs text-gray-400">Loaded Models</span>
        <div className="flex flex-wrap gap-1.5 mt-1">
          {(state?.loadedModels ?? []).length > 0 ? (
            state?.loadedModels.map((m) => (
              <span key={m} className="text-[10px] bg-violet-900/50 text-violet-300 px-2 py-0.5 rounded-full border border-violet-700">{m}</span>
            ))
          ) : (
            <span className="text-xs text-gray-500">No models loaded</span>
          )}
        </div>
      </div>

      {/* Last Thought */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-3">
        <span className="text-xs text-gray-400">Last Thought</span>
        <p className="text-sm text-gray-300 mt-1 italic">{state?.lastThought}</p>
      </div>

      {/* Next Intent */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-3">
        <span className="text-xs text-gray-400">Next Intent</span>
        <p className="text-sm text-cyan-300 mt-1">{state?.nextIntent}</p>
      </div>
    </div>
  );
}
