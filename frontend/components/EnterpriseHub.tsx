import React, { useState } from "react";

interface Feature {
  id: string;
  title: string;
  description: string;
  icon: string;
  color: string;
  status: "available" | "beta" | "coming_soon";
}

const FEATURES: Feature[] = [
  { id: "portfolio", title: "Portfolio Optimizer", description: "Markowitz optimization, efficient frontier analysis, and multi-asset allocation engine.", icon: "\u0398", color: "#06b6d4", status: "available" },
  { id: "risk", title: "Risk Engine", description: "VaR, CVaR, Monte Carlo simulations, and tail-risk analysis for institutional portfolios.", icon: "\u26A0", color: "#ef4444", status: "available" },
  { id: "quant", title: "Quant Strategies", description: "Algorithmic trading strategies: mean reversion, momentum, statistical arbitrage.", icon: "\u03BB", color: "#8b5cf6", status: "available" },
  { id: "backtest", title: "Backtesting Engine", description: "Historical simulation with realistic slippage, fees, and market impact modeling.", icon: "\u23F1", color: "#22c55e", status: "beta" },
  { id: "stress", title: "Stress Testing", description: "Multi-scenario stress tests: 2008 crisis, COVID crash, custom black swan events.", icon: "\u26A1", color: "#f59e0b", status: "beta" },
  { id: "macro", title: "Macro Intelligence", description: "VAR models, GARCH volatility, CPI/GDP tracking and central bank policy analysis.", icon: "\u2318", color: "#ec4899", status: "coming_soon" },
];

const STATUS_BADGE: Record<string, { label: string; style: string }> = {
  available:   { label: "Available", style: "bg-green-900/50 text-green-400 border-green-700" },
  beta:        { label: "Beta", style: "bg-yellow-900/50 text-yellow-400 border-yellow-700" },
  coming_soon: { label: "Coming Soon", style: "bg-gray-800 text-gray-500 border-gray-700" },
};

export default function EnterpriseHub() {
  const [expanded, setExpanded] = useState<string | null>(null);
  const [loading, setLoading] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, string>>({});

  const launchFeature = async (id: string) => {
    if (loading) return;
    setLoading(id);
    try {
      const res = await fetch(`/api/v1/enterprise/${id}/launch`, { method: "POST" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResults((prev) => ({ ...prev, [id]: data.message ?? "Launched successfully" }));
    } catch (e: any) {
      setResults((prev) => ({ ...prev, [id]: `Error: ${e.message}` }));
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="bg-gray-900 text-white rounded-2xl shadow-lg p-6 space-y-5">
      <div>
        <h2 className="text-xl font-bold">Enterprise Hub</h2>
        <p className="text-sm text-gray-400 mt-1">Institutional-grade tools for Bruce Wayne AI</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {FEATURES.map((f) => {
          const isExpanded = expanded === f.id;
          const badge = STATUS_BADGE[f.status];
          return (
            <div key={f.id}
              onClick={() => setExpanded(isExpanded ? null : f.id)}
              className={`bg-gray-800 border rounded-xl p-4 cursor-pointer transition-all duration-200 ${
                isExpanded ? "border-cyan-500 ring-1 ring-cyan-500/30" : "border-gray-700 hover:border-gray-600"
              }`}>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center text-lg"
                    style={{ backgroundColor: `${f.color}20`, color: f.color }}>
                    {f.icon}
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm">{f.title}</h3>
                    <span className={`text-xs px-1.5 py-0.5 rounded border ${badge.style}`}>{badge.label}</span>
                  </div>
                </div>
                <span className="text-gray-600 text-sm">{isExpanded ? "\u2212" : "+"}</span>
              </div>

              {isExpanded && (
                <div className="mt-3 space-y-3">
                  <p className="text-sm text-gray-400">{f.description}</p>
                  {f.status !== "coming_soon" && (
                    <button onClick={(e) => { e.stopPropagation(); launchFeature(f.id); }}
                      disabled={loading === f.id}
                      className="w-full py-2 rounded-lg text-sm font-medium transition"
                      style={{ backgroundColor: `${f.color}30`, color: f.color }}>
                      {loading === f.id ? "Launching..." : `Launch ${f.title}`}
                    </button>
                  )}
                  {results[f.id] && (
                    <div className="bg-gray-900 rounded-lg p-2 text-xs text-gray-400">{results[f.id]}</div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
