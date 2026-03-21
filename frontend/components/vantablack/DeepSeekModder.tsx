import React, { useState, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import Badge from "@/components/ui/badge";
import Progress from "@/components/ui/progress";

interface RefactorLog {
  id: string;
  action: string;
  status: "success" | "warning" | "error";
  message: string;
  timestamp: string;
}

interface ModelParams {
  temperature: number;
  topP: number;
  maxTokens: number;
  repetitionPenalty: number;
  contextWindow: number;
}

export default function DeepSeekModder() {
  const [params, setParams] = useState<ModelParams>({
    temperature: 0.7,
    topP: 0.9,
    maxTokens: 2048,
    repetitionPenalty: 1.1,
    contextWindow: 4096,
  });
  const [logs, setLogs] = useState<RefactorLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refactor = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/vantablack/refactor-deepseek", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      });
      if (!res.ok) throw new Error(`Refactor failed (${res.status})`);
      const data = await res.json();
      const newLog: RefactorLog = {
        id: `log-${Date.now()}`,
        action: "Refactor Executed",
        status: "success",
        message: data.msg || "DeepSeek model parameters updated successfully",
        timestamp: new Date().toISOString(),
      };
      setLogs((prev) => [newLog, ...prev].slice(0, 20));
    } catch (err: any) {
      setError(err.message);
      const errLog: RefactorLog = {
        id: `log-${Date.now()}`,
        action: "Refactor Failed",
        status: "error",
        message: err.message,
        timestamp: new Date().toISOString(),
      };
      setLogs((prev) => [errLog, ...prev].slice(0, 20));
    } finally {
      setLoading(false);
    }
  }, [params]);

  const resetDefaults = () => {
    setParams({ temperature: 0.7, topP: 0.9, maxTokens: 2048, repetitionPenalty: 1.1, contextWindow: 4096 });
  };

  const ParamSlider = ({
    label, value, min, max, step, onChange,
  }: {
    label: string; value: number; min: number; max: number; step: number;
    onChange: (v: number) => void;
  }) => (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-zinc-400">{label}</span>
        <span className="font-mono text-zinc-300">{value}</span>
      </div>
      <input
        type="range"
        min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-1.5 rounded-full appearance-none bg-zinc-700 accent-red-500"
      />
    </div>
  );

  return (
    <Card className="bg-gradient-to-br from-zinc-900 to-red-950/20 border-red-800/30">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-white">DeepSeek Model Modifier</h2>
          <Badge variant="warning" size="sm">Advanced</Badge>
        </div>

        <div className="space-y-4 mb-4">
          <ParamSlider
            label="Temperature" value={params.temperature}
            min={0} max={2} step={0.1}
            onChange={(v) => setParams((p) => ({ ...p, temperature: v }))}
          />
          <ParamSlider
            label="Top P" value={params.topP}
            min={0} max={1} step={0.05}
            onChange={(v) => setParams((p) => ({ ...p, topP: v }))}
          />
          <ParamSlider
            label="Max Tokens" value={params.maxTokens}
            min={256} max={8192} step={256}
            onChange={(v) => setParams((p) => ({ ...p, maxTokens: v }))}
          />
          <ParamSlider
            label="Repetition Penalty" value={params.repetitionPenalty}
            min={1} max={2} step={0.05}
            onChange={(v) => setParams((p) => ({ ...p, repetitionPenalty: v }))}
          />
          <ParamSlider
            label="Context Window" value={params.contextWindow}
            min={1024} max={32768} step={1024}
            onChange={(v) => setParams((p) => ({ ...p, contextWindow: v }))}
          />
        </div>

        <div className="flex gap-2 mb-4">
          <button
            onClick={refactor}
            disabled={loading}
            className="flex-1 px-4 py-2 bg-red-700 hover:bg-red-600 rounded-lg text-sm text-white transition-colors disabled:opacity-50"
          >
            {loading ? "Executing..." : "Execute Refactor"}
          </button>
          <button
            onClick={resetDefaults}
            className="px-4 py-2 bg-zinc-700 hover:bg-zinc-600 rounded-lg text-sm text-white transition-colors"
          >
            Reset
          </button>
        </div>

        {error && (
          <div className="mb-4 p-2 rounded-lg bg-red-900/30 border border-red-800/50 text-red-400 text-sm">
            {error}
          </div>
        )}

        {logs.length > 0 && (
          <div className="space-y-2 max-h-48 overflow-y-auto">
            <h3 className="text-sm font-medium text-zinc-400">Execution Log</h3>
            {logs.map((log) => (
              <div key={log.id} className="flex items-start gap-2 p-2 rounded bg-zinc-800/50 text-xs">
                <Badge variant={log.status === "success" ? "success" : log.status === "warning" ? "warning" : "error"} size="sm">
                  {log.status}
                </Badge>
                <div className="flex-1 min-w-0">
                  <p className="text-zinc-300">{log.message}</p>
                  <p className="text-zinc-600 mt-0.5">{new Date(log.timestamp).toLocaleTimeString()}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
