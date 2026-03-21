import React, { useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";

interface SimResult {
  scenario: string;
  portfolioImpact: number;
  recoveryDays: number;
  maxDrawdown: number;
  sectorImpacts: { sector: string; impact: number }[];
  recommendations: string[];
}

const SCENARIOS = [
  { id: "2008_crash", label: "2008 Financial Crisis", icon: "\uD83C\uDFE6", desc: "Lehman collapse, credit freeze, systemic bank failures" },
  { id: "covid", label: "COVID-19 Crash", icon: "\uD83E\uDDA0", desc: "Pandemic sell-off, March 2020 liquidity crisis" },
  { id: "flash_crash", label: "Flash Crash", icon: "\u26A1", desc: "Sudden algorithmic cascade, rapid 10%+ drop" },
  { id: "black_swan", label: "Black Swan Event", icon: "\uD83E\uDDA2", desc: "Unprecedented tail-risk event, market dislocation" },
  { id: "rate_shock", label: "Rate Shock", icon: "\uD83D\uDCC8", desc: "Sudden 300bps rate hike, bond market crash" },
];

export default function CrisisSimulatorPanel() {
  const [scenario, setScenario] = useState("2008_crash");
  const [portfolio, setPortfolio] = useState("100000");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SimResult | null>(null);

  const simulate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("/api/v1/crisis/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario, portfolioValue: Number(portfolio) }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setResult(await res.json());
    } catch (e: any) {
      setError(e.message ?? "Simulation failed");
    } finally {
      setLoading(false);
    }
  };

  const selected = SCENARIOS.find((s) => s.id === scenario);

  return (
    <div className="bg-gray-900 text-white rounded-2xl shadow-lg p-6 space-y-5">
      <h2 className="text-xl font-bold">Crisis Simulator</h2>
      <p className="text-sm text-gray-400">Simulate historical and hypothetical market crises</p>

      {/* Scenario selector */}
      <div className="space-y-2">
        {SCENARIOS.map((s) => (
          <button key={s.id} onClick={() => setScenario(s.id)}
            className={`w-full text-left p-3 rounded-xl border transition ${
              scenario === s.id ? "border-red-500 bg-red-900/20" : "border-gray-700 bg-gray-800 hover:border-gray-600"
            }`}>
            <div className="flex items-center gap-3">
              <span className="text-xl">{s.icon}</span>
              <div>
                <p className="text-sm font-semibold">{s.label}</p>
                <p className="text-xs text-gray-500">{s.desc}</p>
              </div>
            </div>
          </button>
        ))}
      </div>

      {/* Portfolio input */}
      <div>
        <label className="text-xs text-gray-500 mb-1 block">Portfolio Value ($)</label>
        <input type="number" value={portfolio} onChange={(e) => setPortfolio(e.target.value)}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-cyan-500" />
      </div>

      <button onClick={simulate} disabled={loading}
        className="w-full py-2.5 rounded-lg bg-red-600 hover:bg-red-500 disabled:bg-gray-700 disabled:text-gray-500 font-semibold transition">
        {loading ? "Simulating..." : `Simulate ${selected?.label ?? ""}`}
      </button>

      {error && (
        <div className="bg-red-900/40 border border-red-500 text-red-300 rounded-lg p-3 text-sm">{error}</div>
      )}

      {result && (
        <>
          {/* Impact summary */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-gray-800 rounded-xl p-3 text-center">
              <p className="text-xs text-gray-500">Portfolio Impact</p>
              <p className="text-xl font-mono font-bold text-red-400">{(result.portfolioImpact * 100).toFixed(1)}%</p>
            </div>
            <div className="bg-gray-800 rounded-xl p-3 text-center">
              <p className="text-xs text-gray-500">Max Drawdown</p>
              <p className="text-xl font-mono font-bold text-yellow-400">{(result.maxDrawdown * 100).toFixed(1)}%</p>
            </div>
            <div className="bg-gray-800 rounded-xl p-3 text-center">
              <p className="text-xs text-gray-500">Recovery (days)</p>
              <p className="text-xl font-mono font-bold text-cyan-400">{result.recoveryDays}</p>
            </div>
          </div>

          {/* Sector Impact Chart */}
          <div className="bg-gray-800 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-gray-400 mb-2">Sector Impact</h3>
            <ResponsiveContainer width="100%" height={160}>
              <BarChart data={result.sectorImpacts} layout="vertical">
                <XAxis type="number" tick={{ fill: "#9ca3af", fontSize: 10 }} tickFormatter={(v) => `${v}%`} />
                <YAxis type="category" dataKey="sector" tick={{ fill: "#9ca3af", fontSize: 10 }} width={80} />
                <Tooltip contentStyle={{ backgroundColor: "#1f2937", border: "none", color: "#fff" }}
                  formatter={(v: number) => `${v.toFixed(1)}%`} />
                <Bar dataKey="impact">
                  {result.sectorImpacts.map((entry, i) => (
                    <Cell key={i} fill={entry.impact < -20 ? "#ef4444" : entry.impact < -10 ? "#f59e0b" : "#22c55e"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Recommendations */}
          <div className="bg-gray-800 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-gray-400 mb-2">Hedging Recommendations</h3>
            <ul className="space-y-1.5">
              {result.recommendations.map((r, i) => (
                <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                  <span className="text-cyan-400 mt-0.5">&#x2022;</span>
                  {r}
                </li>
              ))}
            </ul>
          </div>
        </>
      )}
    </div>
  );
}
