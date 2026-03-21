import React, { useState, useEffect, useCallback } from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";

interface MacroData {
  var_forecast: { date: string; value: number }[];
  garch_volatility: number;
  indicators: { name: string; value: number; trend: string }[];
  cpi_trend: { date: string; cpi: number; gdp: number }[];
}

export default function MacroModelPanel() {
  const [data, setData] = useState<MacroData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"forecast" | "indicators" | "trends">("forecast");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/v1/macro-model");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setData(await res.json());
    } catch (e: any) {
      setError(e.message ?? "Failed to load macro data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const tabs = [
    { key: "forecast" as const, label: "VAR Forecast" },
    { key: "indicators" as const, label: "Macro Indicators" },
    { key: "trends" as const, label: "CPI / GDP Trends" },
  ];

  const trendIcon = (t: string) =>
    t === "up" ? "text-green-400" : t === "down" ? "text-red-400" : "text-gray-400";
  const trendArrow = (t: string) =>
    t === "up" ? "\u2191" : t === "down" ? "\u2193" : "\u2192";

  return (
    <div className="bg-gray-900 text-white rounded-2xl shadow-lg p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Econometric Models</h2>
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
        <div className="bg-red-900/40 border border-red-500 text-red-300 rounded-lg p-4">
          <p className="font-semibold">Error</p>
          <p className="text-sm">{error}</p>
          <button onClick={fetchData} className="mt-2 text-sm underline hover:text-red-200">Retry</button>
        </div>
      )}

      {!loading && !error && data && (
        <>
          {/* GARCH badge */}
          <div className="bg-gray-800 rounded-xl p-4 flex items-center justify-between">
            <span className="text-sm text-gray-400">GARCH Volatility</span>
            <span className={`text-2xl font-mono font-bold ${data.garch_volatility > 0.3 ? "text-red-400" : data.garch_volatility > 0.15 ? "text-yellow-400" : "text-green-400"}`}>
              {(data.garch_volatility * 100).toFixed(2)}%
            </span>
          </div>

          {/* Tabs */}
          <div className="flex gap-2">
            {tabs.map((t) => (
              <button key={t.key} onClick={() => setActiveTab(t.key)}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition ${activeTab === t.key ? "bg-cyan-600 text-white" : "bg-gray-800 text-gray-400 hover:bg-gray-700"}`}>
                {t.label}
              </button>
            ))}
          </div>

          {/* VAR Forecast chart */}
          {activeTab === "forecast" && (
            <div className="bg-gray-800 rounded-xl p-4">
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={data.var_forecast}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="date" tick={{ fill: "#9ca3af", fontSize: 10 }} />
                  <YAxis tick={{ fill: "#9ca3af", fontSize: 10 }} />
                  <Tooltip contentStyle={{ backgroundColor: "#1f2937", border: "none", color: "#fff" }} />
                  <Line type="monotone" dataKey="value" stroke="#06b6d4" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Macro indicators table */}
          {activeTab === "indicators" && (
            <div className="bg-gray-800 rounded-xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-700 text-gray-400">
                    <th className="text-left p-3">Indicator</th>
                    <th className="text-right p-3">Value</th>
                    <th className="text-center p-3">Trend</th>
                  </tr>
                </thead>
                <tbody>
                  {data.indicators.map((ind) => (
                    <tr key={ind.name} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                      <td className="p-3 font-medium">{ind.name}</td>
                      <td className="p-3 text-right font-mono">{ind.value.toFixed(2)}</td>
                      <td className={`p-3 text-center font-bold ${trendIcon(ind.trend)}`}>
                        {trendArrow(ind.trend)} {ind.trend}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* CPI / GDP trends */}
          {activeTab === "trends" && (
            <div className="bg-gray-800 rounded-xl p-4">
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={data.cpi_trend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="date" tick={{ fill: "#9ca3af", fontSize: 10 }} />
                  <YAxis tick={{ fill: "#9ca3af", fontSize: 10 }} />
                  <Tooltip contentStyle={{ backgroundColor: "#1f2937", border: "none", color: "#fff" }} />
                  <Line type="monotone" dataKey="cpi" stroke="#f59e0b" strokeWidth={2} dot={false} name="CPI" />
                  <Line type="monotone" dataKey="gdp" stroke="#22c55e" strokeWidth={2} dot={false} name="GDP" />
                </LineChart>
              </ResponsiveContainer>
              <div className="flex gap-4 mt-2 justify-center text-xs text-gray-400">
                <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-amber-500 inline-block" /> CPI</span>
                <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-green-500 inline-block" /> GDP</span>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
