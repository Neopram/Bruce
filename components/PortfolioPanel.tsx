import React, { useState, useEffect, useCallback } from "react";
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
} from "recharts";

interface Holding {
  symbol: string;
  name: string;
  quantity: number;
  price: number;
  value: number;
  allocation: number;
  change24h: number;
  pnl: number;
}

interface PortfolioData {
  totalValue: number;
  change24h: number;
  totalPnl: number;
  holdings: Holding[];
}

const PIE_COLORS = ["#06b6d4", "#8b5cf6", "#22c55e", "#f59e0b", "#ef4444", "#ec4899", "#14b8a6", "#f97316", "#6366f1", "#84cc16"];

export default function PortfolioPanel() {
  const [data, setData] = useState<PortfolioData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<"value" | "change" | "allocation">("value");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/v1/portfolio");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setData(await res.json());
    } catch (e: any) {
      setError(e.message ?? "Failed to load portfolio");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const sorted = data?.holdings ? [...data.holdings].sort((a, b) => {
    if (sortBy === "value") return b.value - a.value;
    if (sortBy === "change") return b.change24h - a.change24h;
    return b.allocation - a.allocation;
  }) : [];

  return (
    <div className="bg-gray-900 text-white rounded-2xl shadow-lg p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Portfolio Overview</h2>
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
          <p className="text-sm">{error}</p>
          <button onClick={fetchData} className="mt-2 text-sm underline hover:text-red-200">Retry</button>
        </div>
      )}

      {!loading && !error && data && (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-gray-800 rounded-xl p-3 text-center">
              <p className="text-xs text-gray-500">Total Value</p>
              <p className="text-xl font-mono font-bold text-white">${data.totalValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
            </div>
            <div className="bg-gray-800 rounded-xl p-3 text-center">
              <p className="text-xs text-gray-500">24h Change</p>
              <p className={`text-xl font-mono font-bold ${data.change24h >= 0 ? "text-green-400" : "text-red-400"}`}>
                {data.change24h >= 0 ? "+" : ""}{data.change24h.toFixed(2)}%
              </p>
            </div>
            <div className="bg-gray-800 rounded-xl p-3 text-center">
              <p className="text-xs text-gray-500">Total P&amp;L</p>
              <p className={`text-xl font-mono font-bold ${data.totalPnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                {data.totalPnl >= 0 ? "+" : ""}${data.totalPnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </p>
            </div>
          </div>

          {/* Pie chart */}
          <div className="bg-gray-800 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-gray-400 mb-2">Allocation</h3>
            <div className="flex items-center gap-4">
              <ResponsiveContainer width="50%" height={180}>
                <PieChart>
                  <Pie data={data.holdings} dataKey="allocation" nameKey="symbol" cx="50%" cy="50%"
                    outerRadius={70} innerRadius={35} paddingAngle={2}>
                    {data.holdings.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: "#1f2937", border: "none", color: "#fff" }}
                    formatter={(v: number) => `${v.toFixed(1)}%`} />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex-1 space-y-1 max-h-44 overflow-y-auto">
                {data.holdings.map((h, i) => (
                  <div key={h.symbol} className="flex items-center gap-2 text-xs">
                    <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }} />
                    <span className="flex-1 truncate">{h.symbol}</span>
                    <span className="font-mono text-gray-400">{h.allocation.toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Holdings table */}
          <div className="bg-gray-800 rounded-xl overflow-hidden overflow-x-auto">
            <div className="flex gap-2 p-3">
              {(["value", "change", "allocation"] as const).map((s) => (
                <button key={s} onClick={() => setSortBy(s)}
                  className={`text-xs px-2 py-1 rounded transition ${sortBy === s ? "bg-gray-700 text-white" : "text-gray-500 hover:text-gray-300"}`}>
                  Sort: {s}
                </button>
              ))}
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700 text-gray-400">
                  <th className="text-left p-3">Asset</th>
                  <th className="text-right p-3">Qty</th>
                  <th className="text-right p-3">Price</th>
                  <th className="text-right p-3">Value</th>
                  <th className="text-right p-3">24h</th>
                  <th className="text-right p-3">P&amp;L</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((h) => (
                  <tr key={h.symbol} className="border-t border-gray-700/50 hover:bg-gray-700/30">
                    <td className="p-3">
                      <p className="font-semibold">{h.symbol}</p>
                      <p className="text-xs text-gray-500">{h.name}</p>
                    </td>
                    <td className="p-3 text-right font-mono">{h.quantity}</td>
                    <td className="p-3 text-right font-mono">${h.price.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                    <td className="p-3 text-right font-mono">${h.value.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                    <td className={`p-3 text-right font-mono ${h.change24h >= 0 ? "text-green-400" : "text-red-400"}`}>
                      {h.change24h >= 0 ? "+" : ""}{h.change24h.toFixed(2)}%
                    </td>
                    <td className={`p-3 text-right font-mono ${h.pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                      {h.pnl >= 0 ? "+" : ""}${h.pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
