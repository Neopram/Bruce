import React, { useEffect, useState, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface ModelInfo {
  id: string;
  name: string;
  status: "loaded" | "unloaded" | "loading" | "error";
  tokensPerSec: number;
  latencyMs: number;
  gpuUsage: number;
  cpuUsage: number;
  memoryMb: number;
}

const STATUS_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  loaded: { bg: "bg-green-900/40", text: "text-green-400", label: "LOADED" },
  unloaded: { bg: "bg-gray-800", text: "text-gray-500", label: "UNLOADED" },
  loading: { bg: "bg-yellow-900/30", text: "text-yellow-400", label: "LOADING" },
  error: { bg: "bg-red-900/30", text: "text-red-400", label: "ERROR" },
};

function UsageBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-gray-400 w-10">{label}</span>
      <div className="flex-1 h-2 bg-gray-700 rounded overflow-hidden">
        <div className={`h-full rounded ${color}`} style={{ width: `${Math.min(value, 100)}%` }} />
      </div>
      <span className="text-gray-300 w-10 text-right">{value.toFixed(0)}%</span>
    </div>
  );
}

export default function NeuralHUD() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeModel, setActiveModel] = useState<string | null>(null);

  const fetchModels = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/bruce-api/inference/models`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const modelList: ModelInfo[] = (data.models || data || []).map((m: any) => ({
        id: m.id || m.name,
        name: m.name || m.id,
        status: m.status || "unloaded",
        tokensPerSec: m.tokens_per_sec ?? m.tokensPerSec ?? 0,
        latencyMs: m.latency_ms ?? m.latencyMs ?? 0,
        gpuUsage: m.gpu_usage ?? m.gpuUsage ?? 0,
        cpuUsage: m.cpu_usage ?? m.cpuUsage ?? 0,
        memoryMb: m.memory_mb ?? m.memoryMb ?? 0,
      }));
      setModels(modelList);
      const active = modelList.find((m) => m.status === "loaded");
      if (active) setActiveModel(active.id);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to fetch model info");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchModels();
    const interval = setInterval(fetchModels, 5000);
    return () => clearInterval(interval);
  }, [fetchModels]);

  if (loading) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 animate-pulse">
        <div className="h-4 bg-gray-700 rounded w-1/3 mb-4" />
        <div className="space-y-3">
          {[1, 2, 3].map((i) => <div key={i} className="h-16 bg-gray-800 rounded" />)}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-900 border border-red-800 rounded-xl p-6">
        <h2 className="text-lg font-bold text-red-400">Neural HUD</h2>
        <p className="text-red-300 text-sm mt-2">{error}</p>
        <button onClick={fetchModels} className="mt-3 px-3 py-1 bg-red-700 hover:bg-red-600 text-white text-sm rounded">Retry</button>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-cyan-300">Neural HUD</h2>
        <span className="text-xs text-gray-500">{models.length} model(s)</span>
      </div>

      <div className="space-y-3">
        {models.map((model) => {
          const style = STATUS_STYLES[model.status] || STATUS_STYLES.unloaded;
          const isActive = model.id === activeModel;
          return (
            <div
              key={model.id}
              className={`p-3 rounded-lg border ${isActive ? "border-cyan-600 ring-1 ring-cyan-600/30" : "border-gray-700"} ${style.bg}`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${model.status === "loaded" ? "bg-green-400 animate-pulse" : model.status === "loading" ? "bg-yellow-400 animate-pulse" : "bg-gray-600"}`} />
                  <span className="text-sm font-medium text-gray-200">{model.name}</span>
                  {isActive && <span className="text-[10px] bg-cyan-800 text-cyan-200 px-1.5 py-0.5 rounded">ACTIVE</span>}
                </div>
                <span className={`text-xs font-mono ${style.text}`}>{style.label}</span>
              </div>

              {model.status === "loaded" && (
                <div className="space-y-1.5">
                  <div className="flex gap-4 text-xs text-gray-400">
                    <span>Tokens/s: <span className="text-cyan-300 font-mono">{model.tokensPerSec.toFixed(1)}</span></span>
                    <span>Latency: <span className="text-cyan-300 font-mono">{model.latencyMs.toFixed(0)}ms</span></span>
                    <span>VRAM: <span className="text-cyan-300 font-mono">{model.memoryMb.toFixed(0)}MB</span></span>
                  </div>
                  <UsageBar label="GPU" value={model.gpuUsage} color="bg-green-500" />
                  <UsageBar label="CPU" value={model.cpuUsage} color="bg-blue-500" />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {models.length === 0 && (
        <p className="text-gray-500 text-sm text-center py-4">No models registered</p>
      )}
    </div>
  );
}
