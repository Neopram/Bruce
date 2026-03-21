import React, { useState, useEffect, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface DecisionNode {
  id: string;
  timestamp: string;
  label: string;
  confidence: number;
  outcome: "positive" | "negative" | "neutral" | "pending";
  reasoning: string;
  children?: DecisionNode[];
}

const OUTCOME_STYLES: Record<string, { text: string; bg: string; dot: string }> = {
  positive: { text: "text-green-400", bg: "bg-green-900/20", dot: "bg-green-500" },
  negative: { text: "text-red-400", bg: "bg-red-900/20", dot: "bg-red-500" },
  neutral: { text: "text-gray-400", bg: "bg-gray-800/40", dot: "bg-gray-500" },
  pending: { text: "text-yellow-400", bg: "bg-yellow-900/20", dot: "bg-yellow-500" },
};

function DecisionNodeItem({ node, depth = 0 }: { node: DecisionNode; depth?: number }) {
  const [expanded, setExpanded] = useState(depth < 1);
  const style = OUTCOME_STYLES[node.outcome];
  const hasChildren = node.children && node.children.length > 0;

  return (
    <div className={depth > 0 ? "ml-4 border-l border-gray-700 pl-3" : ""}>
      <div
        className={`${style.bg} border border-gray-700 rounded-lg p-3 mb-2 cursor-pointer hover:border-gray-600 transition-colors`}
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            {hasChildren && <span className="text-[10px] text-gray-500">{expanded ? "[-]" : "[+]"}</span>}
            <span className={`w-2 h-2 rounded-full ${style.dot}`} />
            <span className="text-sm font-semibold text-gray-200">{node.label}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-[10px] ${style.text}`}>{node.outcome.toUpperCase()}</span>
            <span className="text-[10px] text-gray-600 font-mono">{node.timestamp.slice(11, 19)}</span>
          </div>
        </div>

        {/* Confidence bar */}
        <div className="flex items-center gap-2 mb-1">
          <span className="text-[10px] text-gray-500 w-16">Confidence</span>
          <div className="flex-1 h-1.5 bg-gray-700 rounded overflow-hidden">
            <div
              className={`h-full rounded ${node.confidence > 0.7 ? "bg-green-500" : node.confidence > 0.4 ? "bg-yellow-500" : "bg-red-500"}`}
              style={{ width: `${node.confidence * 100}%` }}
            />
          </div>
          <span className="text-[10px] text-gray-400">{(node.confidence * 100).toFixed(0)}%</span>
        </div>

        <p className="text-xs text-gray-400 leading-relaxed">{node.reasoning}</p>
      </div>

      {expanded && hasChildren && (
        <div className="space-y-0">
          {node.children!.map((child) => (
            <DecisionNodeItem key={child.id} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function AgentDecisionView() {
  const [decisions, setDecisions] = useState<DecisionNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<"1h" | "6h" | "24h">("6h");

  const fetchDecisions = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/agents/decisions?range=${timeRange}`);
      if (!res.ok) throw new Error();
      const data = await res.json();
      setDecisions(data.decisions || data || []);
    } catch {
      setDecisions([
        {
          id: "d1", timestamp: new Date(Date.now() - 3600000).toISOString(), label: "Portfolio Rebalance Analysis",
          confidence: 0.85, outcome: "positive", reasoning: "Detected overexposure to BTC (45% vs target 30%). Recommended reducing position.",
          children: [
            { id: "d1a", timestamp: new Date(Date.now() - 3500000).toISOString(), label: "Sell 15% BTC Holdings", confidence: 0.82, outcome: "positive", reasoning: "Market conditions support gradual exit. Volume sufficient for minimal slippage." },
            { id: "d1b", timestamp: new Date(Date.now() - 3400000).toISOString(), label: "Reallocate to ETH", confidence: 0.68, outcome: "neutral", reasoning: "ETH/BTC ratio showing mean reversion potential. Moderate confidence." },
          ],
        },
        {
          id: "d2", timestamp: new Date(Date.now() - 1800000).toISOString(), label: "Risk Alert: Leverage Check",
          confidence: 0.92, outcome: "negative", reasoning: "Current leverage at 3.2x exceeds safe threshold of 2.5x. Immediate deleveraging recommended.",
          children: [
            { id: "d2a", timestamp: new Date(Date.now() - 1700000).toISOString(), label: "Close Margined Positions", confidence: 0.88, outcome: "pending", reasoning: "Closing lowest-conviction margined positions first to reduce risk." },
          ],
        },
        {
          id: "d3", timestamp: new Date(Date.now() - 600000).toISOString(), label: "Sentiment Opportunity",
          confidence: 0.71, outcome: "pending", reasoning: "Extreme fear index (22) with positive on-chain signals. Historical pattern suggests buying opportunity.",
        },
      ]);
    }
    setLoading(false);
  }, [timeRange]);

  useEffect(() => { fetchDecisions(); }, [fetchDecisions]);

  const outcomes = decisions.reduce((acc, d) => {
    acc[d.outcome] = (acc[d.outcome] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  if (loading) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 animate-pulse space-y-3">
        <div className="h-4 bg-gray-700 rounded w-1/3" />
        {[1, 2, 3].map((i) => <div key={i} className="h-20 bg-gray-800 rounded" />)}
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-emerald-300">Agent Decisions</h2>
        <div className="flex gap-1">
          {(["1h", "6h", "24h"] as const).map((r) => (
            <button
              key={r}
              onClick={() => setTimeRange(r)}
              className={`text-[10px] px-2 py-1 rounded ${timeRange === r ? "bg-emerald-800 text-emerald-200" : "bg-gray-800 text-gray-500 hover:bg-gray-700"}`}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      {/* Summary */}
      <div className="flex gap-3">
        {Object.entries(outcomes).map(([outcome, count]) => {
          const s = OUTCOME_STYLES[outcome];
          return (
            <div key={outcome} className="flex items-center gap-1.5 text-xs">
              <span className={`w-2 h-2 rounded-full ${s.dot}`} />
              <span className={s.text}>{outcome}: {count}</span>
            </div>
          );
        })}
      </div>

      {/* Decision Tree */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {decisions.map((d) => <DecisionNodeItem key={d.id} node={d} />)}
        {decisions.length === 0 && <p className="text-gray-600 text-sm text-center py-8">No decisions in this time range</p>}
      </div>
    </div>
  );
}
