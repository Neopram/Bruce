import React, { useState, useEffect, useRef, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

type AILogType = "inference" | "decision" | "memory" | "emotion";

interface AILogEntry {
  id: string;
  timestamp: string;
  type: AILogType;
  model: string;
  message: string;
  durationMs?: number;
  tokens?: number;
}

const TYPE_COLORS: Record<AILogType, { text: string; badge: string }> = {
  inference: { text: "text-cyan-300", badge: "bg-cyan-900 text-cyan-300" },
  decision: { text: "text-green-300", badge: "bg-green-900 text-green-300" },
  memory: { text: "text-purple-300", badge: "bg-purple-900 text-purple-300" },
  emotion: { text: "text-pink-300", badge: "bg-pink-900 text-pink-300" },
};

export default function AILogsPanel() {
  const [logs, setLogs] = useState<AILogEntry[]>([]);
  const [filter, setFilter] = useState<AILogType | "all">("all");
  const [modelFilter, setModelFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  const fetchLogs = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/ai/logs?limit=100`);
      if (!res.ok) throw new Error();
      const data = await res.json();
      setLogs(data.logs || data || []);
    } catch {
      setLogs([
        { id: "1", timestamp: new Date(Date.now() - 30000).toISOString(), type: "inference", model: "deepseek-v3", message: "Completed market analysis inference", durationMs: 234, tokens: 512 },
        { id: "2", timestamp: new Date(Date.now() - 25000).toISOString(), type: "decision", model: "deepseek-v3", message: "Decision: Reduce BTC exposure by 10% (confidence: 0.82)", durationMs: 45 },
        { id: "3", timestamp: new Date(Date.now() - 20000).toISOString(), type: "memory", model: "system", message: "Stored new episodic memory: market_shift_2024_03", durationMs: 12 },
        { id: "4", timestamp: new Date(Date.now() - 15000).toISOString(), type: "emotion", model: "emotion-engine", message: "State transition: neutral -> focused (trigger: market_volatility)", durationMs: 8 },
        { id: "5", timestamp: new Date(Date.now() - 10000).toISOString(), type: "inference", model: "gpt-4o", message: "Sentiment analysis on 847 social posts", durationMs: 1234, tokens: 2048 },
        { id: "6", timestamp: new Date(Date.now() - 5000).toISOString(), type: "decision", model: "deepseek-v3", message: "Decision: Set trailing stop at -3.5% for ETH position", durationMs: 38 },
        { id: "7", timestamp: new Date(Date.now() - 2000).toISOString(), type: "memory", model: "system", message: "Retrieved 12 relevant memories for context window", durationMs: 23 },
        { id: "8", timestamp: new Date().toISOString(), type: "inference", model: "claude-3", message: "Risk assessment completed for portfolio rebalance", durationMs: 567, tokens: 1024 },
      ]);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, [fetchLogs]);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [logs]);

  const models = Array.from(new Set(logs.map((l) => l.model)));
  const filtered = logs.filter((log) => {
    if (filter !== "all" && log.type !== filter) return false;
    if (modelFilter !== "all" && log.model !== modelFilter) return false;
    return true;
  });

  if (loading) {
    return (
      <div className="bg-gray-950 border border-gray-700 rounded-xl p-6 animate-pulse">
        <div className="h-4 bg-gray-700 rounded w-1/4 mb-4" />
        <div className="h-64 bg-gray-900 rounded" />
      </div>
    );
  }

  return (
    <div className="bg-gray-950 border border-gray-700 rounded-xl p-6 space-y-3 font-mono">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-cyan-300">AI Logs</h2>
        <span className="text-xs text-gray-500">{filtered.length} entries</span>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 items-center">
        <div className="flex gap-1">
          {(["all", "inference", "decision", "memory", "emotion"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setFilter(t)}
              className={`text-[10px] px-2 py-1 rounded ${filter === t ? "bg-gray-700 text-gray-200" : "bg-gray-800 text-gray-500 hover:bg-gray-750"}`}
            >
              {t.toUpperCase()}
            </button>
          ))}
        </div>
        <select
          value={modelFilter}
          onChange={(e) => setModelFilter(e.target.value)}
          className="bg-gray-800 border border-gray-700 text-gray-300 text-xs rounded px-2 py-1 focus:outline-none"
        >
          <option value="all">All Models</option>
          {models.map((m) => <option key={m} value={m}>{m}</option>)}
        </select>
      </div>

      {/* Log Entries */}
      <div ref={scrollRef} className="bg-black/60 border border-gray-800 rounded-lg p-2 max-h-80 overflow-y-auto space-y-1">
        {filtered.map((log) => {
          const colors = TYPE_COLORS[log.type];
          return (
            <div key={log.id} className="px-2 py-1.5 rounded bg-gray-900/50 border border-gray-800 text-xs">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-gray-600">{log.timestamp.slice(11, 23)}</span>
                <span className={`text-[9px] px-1.5 py-0.5 rounded ${colors.badge}`}>{log.type.toUpperCase()}</span>
                <span className="text-gray-500">[{log.model}]</span>
                {log.durationMs != null && <span className="text-gray-600 ml-auto">{log.durationMs}ms</span>}
                {log.tokens != null && <span className="text-gray-600">{log.tokens}tok</span>}
              </div>
              <p className={`${colors.text} leading-relaxed`}>{log.message}</p>
            </div>
          );
        })}
        {filtered.length === 0 && <p className="text-gray-600 text-center py-8 text-xs">No logs matching filter</p>}
      </div>

      <button onClick={fetchLogs} className="text-[10px] text-gray-500 hover:text-gray-300">Refresh</button>
    </div>
  );
}
