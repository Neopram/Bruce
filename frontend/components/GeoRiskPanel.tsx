import React, { useState, useEffect, useCallback } from "react";

interface Region {
  id: string;
  name: string;
  riskScore: number;
  trend: "rising" | "stable" | "falling";
  keyRisks: string[];
  marketImpact: string;
}

const REGIONS: Region[] = [
  { id: "na", name: "North America", riskScore: 25, trend: "stable", keyRisks: ["Fiscal policy uncertainty", "Tech regulation"], marketImpact: "USD strength, equity volatility" },
  { id: "eu", name: "Europe", riskScore: 45, trend: "rising", keyRisks: ["Energy dependency", "ECB policy shifts"], marketImpact: "EUR weakness, bond spread widening" },
  { id: "asia", name: "East Asia", riskScore: 55, trend: "rising", keyRisks: ["Taiwan strait tensions", "China slowdown"], marketImpact: "Supply chain disruption, commodity swings" },
  { id: "mena", name: "Middle East", riskScore: 72, trend: "rising", keyRisks: ["Regional conflicts", "Oil supply risk"], marketImpact: "Oil price spikes, safe-haven flows" },
  { id: "sa", name: "South America", riskScore: 48, trend: "stable", keyRisks: ["Currency instability", "Political shifts"], marketImpact: "EM bond yields, commodity prices" },
  { id: "africa", name: "Sub-Saharan Africa", riskScore: 38, trend: "falling", keyRisks: ["Debt sustainability", "Resource competition"], marketImpact: "Mining stocks, frontier market bonds" },
  { id: "seasia", name: "Southeast Asia", riskScore: 30, trend: "stable", keyRisks: ["Trade route disruption", "Currency volatility"], marketImpact: "Manufacturing shifts, FDI flows" },
  { id: "russia", name: "Russia / CIS", riskScore: 85, trend: "rising", keyRisks: ["Sanctions escalation", "Energy weaponization"], marketImpact: "Gas prices, grain markets" },
];

const riskColor = (score: number) =>
  score >= 70 ? "#ef4444" : score >= 50 ? "#f59e0b" : score >= 30 ? "#facc15" : "#22c55e";

const trendArrow = (t: string) =>
  t === "rising" ? "\u2191" : t === "falling" ? "\u2193" : "\u2192";

export default function GeoRiskPanel() {
  const [regions, setRegions] = useState<Region[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/v1/geo/risks");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setRegions(data.regions ?? REGIONS);
    } catch {
      setRegions(REGIONS);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const selectedRegion = regions.find((r) => r.id === selected);

  return (
    <div className="bg-gray-900 text-white rounded-2xl shadow-lg p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Geopolitical Risk Map</h2>
        <button onClick={fetchData} className="px-3 py-1 text-sm rounded bg-gray-700 hover:bg-gray-600 transition">
          Refresh
        </button>
      </div>

      {loading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin h-8 w-8 border-4 border-cyan-400 border-t-transparent rounded-full" />
        </div>
      )}

      {error && (
        <div className="bg-red-900/40 border border-red-500 text-red-300 rounded-lg p-3 text-sm">{error}</div>
      )}

      {!loading && (
        <>
          {/* Region Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {regions.map((r) => (
              <button key={r.id} onClick={() => setSelected(selected === r.id ? null : r.id)}
                className={`p-3 rounded-xl border text-left transition ${
                  selected === r.id ? "border-cyan-500 ring-1 ring-cyan-500/30" : "border-gray-700 hover:border-gray-600"
                }`}
                style={{ backgroundColor: `${riskColor(r.riskScore)}10` }}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-gray-400 truncate">{r.name}</span>
                  <span className={`text-xs ${r.trend === "rising" ? "text-red-400" : r.trend === "falling" ? "text-green-400" : "text-gray-400"}`}>
                    {trendArrow(r.trend)}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div className="h-2 rounded-full transition-all" style={{ width: `${r.riskScore}%`, backgroundColor: riskColor(r.riskScore) }} />
                  </div>
                  <span className="text-sm font-mono font-bold" style={{ color: riskColor(r.riskScore) }}>
                    {r.riskScore}
                  </span>
                </div>
              </button>
            ))}
          </div>

          {/* Legend */}
          <div className="flex gap-4 justify-center text-xs text-gray-500">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500" /> Low (0-29)</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-400" /> Medium (30-49)</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500" /> High (50-69)</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" /> Critical (70+)</span>
          </div>

          {/* Selected region detail */}
          {selectedRegion && (
            <div className="bg-gray-800 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">{selectedRegion.name}</h3>
                <span className="text-2xl font-mono font-bold" style={{ color: riskColor(selectedRegion.riskScore) }}>
                  {selectedRegion.riskScore}/100
                </span>
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-1">Key Risks</p>
                <ul className="space-y-1">
                  {selectedRegion.keyRisks.map((r, i) => (
                    <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                      <span className="text-red-400 mt-0.5">&#x2022;</span>{r}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-1">Market Impact</p>
                <p className="text-sm text-gray-300">{selectedRegion.marketImpact}</p>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
