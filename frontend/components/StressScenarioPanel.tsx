import React, { useState } from "react";

interface ScenarioResult {
  name: string;
  portfolioImpact: number;
  varImpact: number;
  volatilitySpike: number;
  recoveryWeeks: number;
  severity: "low" | "medium" | "high" | "extreme";
}

interface StressResults {
  scenarios: ScenarioResult[];
  worstCase: string;
  hedgingRecommendations: string[];
}

const SCENARIOS = [
  { id: "2008", label: "2008 Financial Crisis" },
  { id: "covid", label: "COVID-19 Pandemic" },
  { id: "dotcom", label: "Dot-com Bubble" },
  { id: "rate_hike", label: "Aggressive Rate Hike" },
  { id: "currency_crisis", label: "EM Currency Crisis" },
  { id: "black_swan", label: "Black Swan Event" },
];

const SEVERITY_COLORS: Record<string, string> = {
  low: "text-green-400 bg-green-900/30",
  medium: "text-yellow-400 bg-yellow-900/30",
  high: "text-orange-400 bg-orange-900/30",
  extreme: "text-red-400 bg-red-900/30",
};

export default function StressScenarioPanel() {
  const [selected, setSelected] = useState<Set<string>>(new Set(SCENARIOS.map((s) => s.id)));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<StressResults | null>(null);

  const toggleScenario = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const runAll = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/v1/stress/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenarios: Array.from(selected) }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setResults(await res.json());
    } catch (e: any) {
      setError(e.message ?? "Stress test failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gray-900 text-white rounded-2xl shadow-lg p-6 space-y-5">
      <h2 className="text-xl font-bold">Stress Scenario Testing</h2>
      <p className="text-sm text-gray-400">Multi-scenario comparison and hedging analysis</p>

      {/* Scenario checkboxes */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
        {SCENARIOS.map((s) => (
          <button key={s.id} onClick={() => toggleScenario(s.id)}
            className={`p-2.5 rounded-lg text-sm border text-left transition ${
              selected.has(s.id) ? "border-purple-500 bg-purple-900/20 text-white" : "border-gray-700 bg-gray-800 text-gray-500 hover:border-gray-600"
            }`}>
            <span className="mr-2">{selected.has(s.id) ? "\u2611" : "\u2610"}</span>
            {s.label}
          </button>
        ))}
      </div>

      <button onClick={runAll} disabled={loading || selected.size === 0}
        className="w-full py-2.5 rounded-lg bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 disabled:text-gray-500 font-semibold transition">
        {loading ? "Running..." : `Run All (${selected.size} scenarios)`}
      </button>

      {error && (
        <div className="bg-red-900/40 border border-red-500 text-red-300 rounded-lg p-3 text-sm">{error}</div>
      )}

      {results && (
        <>
          {/* Worst case highlight */}
          <div className="bg-red-900/20 border border-red-700 rounded-xl p-4 text-center">
            <p className="text-xs text-red-400 mb-1">Worst-Case Scenario</p>
            <p className="text-lg font-bold text-red-300">{results.worstCase}</p>
          </div>

          {/* Comparison table */}
          <div className="bg-gray-800 rounded-xl overflow-hidden overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700 text-gray-400">
                  <th className="text-left p-3">Scenario</th>
                  <th className="text-right p-3">Portfolio</th>
                  <th className="text-right p-3">VaR</th>
                  <th className="text-right p-3">Vol Spike</th>
                  <th className="text-right p-3">Recovery</th>
                  <th className="text-center p-3">Severity</th>
                </tr>
              </thead>
              <tbody>
                {results.scenarios.map((s) => (
                  <tr key={s.name} className={`border-t border-gray-700/50 hover:bg-gray-700/30 ${
                    s.name === results.worstCase ? "bg-red-900/10" : ""
                  }`}>
                    <td className="p-3 font-medium">{s.name}</td>
                    <td className="p-3 text-right font-mono text-red-400">{(s.portfolioImpact * 100).toFixed(1)}%</td>
                    <td className="p-3 text-right font-mono text-yellow-400">{(s.varImpact * 100).toFixed(1)}%</td>
                    <td className="p-3 text-right font-mono text-orange-400">{(s.volatilitySpike * 100).toFixed(0)}%</td>
                    <td className="p-3 text-right font-mono text-gray-300">{s.recoveryWeeks}w</td>
                    <td className="p-3 text-center">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded capitalize ${SEVERITY_COLORS[s.severity] ?? ""}`}>
                        {s.severity}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Hedging Recommendations */}
          <div className="bg-gray-800 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-gray-400 mb-2">Hedging Recommendations</h3>
            <ul className="space-y-1.5">
              {results.hedgingRecommendations.map((r, i) => (
                <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                  <span className="text-purple-400 mt-0.5">&#x2022;</span>
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
