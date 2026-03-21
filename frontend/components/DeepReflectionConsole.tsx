import React, { useEffect, useState, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface ThoughtNode {
  id: string;
  timestamp: string;
  type: "observation" | "analysis" | "decision" | "reflection";
  content: string;
  confidence: number;
  children?: ThoughtNode[];
}

const TYPE_COLORS: Record<string, { border: string; text: string; badge: string }> = {
  observation: { border: "border-blue-700", text: "text-blue-300", badge: "bg-blue-900 text-blue-300" },
  analysis: { border: "border-yellow-700", text: "text-yellow-300", badge: "bg-yellow-900 text-yellow-300" },
  decision: { border: "border-green-700", text: "text-green-300", badge: "bg-green-900 text-green-300" },
  reflection: { border: "border-purple-700", text: "text-purple-300", badge: "bg-purple-900 text-purple-300" },
};

function ThoughtItem({ node, depth = 0 }: { node: ThoughtNode; depth?: number }) {
  const [expanded, setExpanded] = useState(depth < 2);
  const colors = TYPE_COLORS[node.type] || TYPE_COLORS.observation;
  const hasChildren = node.children && node.children.length > 0;

  return (
    <div className={`ml-${Math.min(depth * 4, 12)}`}>
      <div
        className={`border-l-2 ${colors.border} pl-3 py-2 cursor-pointer hover:bg-gray-800/50 rounded-r`}
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2 mb-1">
          <span className={`text-[10px] px-1.5 py-0.5 rounded ${colors.badge}`}>{node.type.toUpperCase()}</span>
          <span className="text-[10px] text-gray-500 font-mono">{node.timestamp}</span>
          {hasChildren && <span className="text-[10px] text-gray-500">{expanded ? "[-]" : `[+${node.children!.length}]`}</span>}
        </div>
        <p className="text-sm text-gray-300 font-mono leading-relaxed">{node.content}</p>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-[10px] text-gray-500">Quality:</span>
          <div className="w-16 h-1.5 bg-gray-700 rounded overflow-hidden">
            <div
              className={`h-full rounded ${node.confidence > 0.7 ? "bg-green-500" : node.confidence > 0.4 ? "bg-yellow-500" : "bg-red-500"}`}
              style={{ width: `${node.confidence * 100}%` }}
            />
          </div>
          <span className="text-[10px] text-gray-400">{(node.confidence * 100).toFixed(0)}%</span>
        </div>
      </div>
      {expanded && hasChildren && (
        <div className="mt-1 space-y-1">
          {node.children!.map((child) => (
            <ThoughtItem key={child.id} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function DeepReflectionConsole() {
  const [thoughts, setThoughts] = useState<ThoughtNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("all");

  const fetchThoughts = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/bruce-api/reflection/thoughts`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setThoughts(data.thoughts || data || []);
      setError(null);
    } catch {
      setThoughts([
        {
          id: "t1", timestamp: new Date(Date.now() - 60000).toISOString().slice(11, 19), type: "observation",
          content: "Market volatility increasing. BTC price diverging from 200-day MA.", confidence: 0.85,
          children: [
            { id: "t1a", timestamp: new Date(Date.now() - 55000).toISOString().slice(11, 19), type: "analysis", content: "RSI at 72, approaching overbought. Volume declining on uptick.", confidence: 0.78 },
            { id: "t1b", timestamp: new Date(Date.now() - 50000).toISOString().slice(11, 19), type: "decision", content: "Reduce position by 15%. Set stop-loss at support level.", confidence: 0.82, children: [
              { id: "t1b1", timestamp: new Date(Date.now() - 45000).toISOString().slice(11, 19), type: "reflection", content: "Decision aligns with risk framework. Confidence within threshold.", confidence: 0.9 },
            ]},
          ],
        },
        {
          id: "t2", timestamp: new Date(Date.now() - 30000).toISOString().slice(11, 19), type: "observation",
          content: "Sentiment shift detected in social feeds. Fear index rising.", confidence: 0.72,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchThoughts(); }, [fetchThoughts]);

  const filtered = filter === "all" ? thoughts : thoughts.filter((t) => t.type === filter);

  if (loading) {
    return (
      <div className="bg-gray-950 border border-gray-700 rounded-xl p-6 animate-pulse space-y-3">
        <div className="h-4 bg-gray-700 rounded w-1/3" />
        {[1, 2, 3].map((i) => <div key={i} className="h-16 bg-gray-800 rounded" />)}
      </div>
    );
  }

  return (
    <div className="bg-gray-950 border border-gray-700 rounded-xl p-6 space-y-4 font-mono">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-green-400">Deep Reflection Console</h2>
        <div className="flex gap-1">
          {["all", "observation", "analysis", "decision", "reflection"].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`text-[10px] px-2 py-1 rounded ${filter === f ? "bg-green-800 text-green-200" : "bg-gray-800 text-gray-400 hover:bg-gray-700"}`}
            >
              {f.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <div className="border border-gray-800 rounded-lg bg-black/40 p-4 max-h-96 overflow-y-auto space-y-2 text-sm" style={{ textShadow: "0 0 1px rgba(34,197,94,0.3)" }}>
        {filtered.length > 0 ? (
          filtered.map((t) => <ThoughtItem key={t.id} node={t} />)
        ) : (
          <p className="text-gray-600 text-center py-8">No thoughts recorded yet.</p>
        )}
      </div>

      {error && <p className="text-red-400 text-xs">{error}</p>}
      <button onClick={fetchThoughts} className="px-3 py-1.5 bg-green-800 hover:bg-green-700 text-green-200 text-xs rounded">Refresh</button>
    </div>
  );
}
