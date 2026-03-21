import React, { useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";

interface BacktestResult {
  equityCurve: { date: string; equity: number }[];
  metrics: {
    sharpe: number;
    maxDrawdown: number;
    winRate: number;
    totalReturn: number;
    cagr: number;
    volatility: number;
    trades: number;
    profitFactor: number;
  };
}

const STRATEGIES = [
  { id: "momentum", label: "Momentum" },
  { id: "mean_reversion", label: "Mean Reversion" },
  { id: "breakout", label: "Breakout" },
  { id: "pairs_trading", label: "Pairs Trading" },
  { id: "rsi_divergence", label: "RSI Divergence" },
];

export default function QuantBacktestPanel() {
  const [strategy, setStrategy] = useState("momentum");
  const [startDate, setStartDate] = useState("2023-01-01");
  const [endDate, setEndDate] = useState("2024-12-31");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BacktestResult | null>(null);

  const runBacktest = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("/api/v1/quant/backtest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ strategy, startDate, endDate }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setResult(await res.json());
    } catch (e: any) {
      setError(e.message ?? "Backtest failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gray-900 text-white rounded-2xl shadow-lg p-6 space-y-5">
      <h2 className="text-xl font-bold">Quantitative Backtest</h2>

      {/* Strategy selector */}
      <div>
        <label className="text-xs text-gray-500 mb-1 block">Strategy</label>
        <div className="flex flex-wrap gap-2">
          {STRATEGIES.map((s) => (
            <button key={s.id} onClick={() => setStrategy(s.id)}
              className={`px-3 py-1.5 rounded-lg text-sm border transition ${
                strategy === s.id ? "border-green-500 bg-gray-800 text-green-400" : "border-gray-700 bg-gray-800/50 text-gray-500 hover:border-gray-600"
              }`}>
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Date range */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Start Date</label>
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-cyan-500" />
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">End Date</label>
          <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-cyan-500" />
        </div>
      </div>

      <button onClick={runBacktest} disabled={loading}
        className="w-full py-2.5 rounded-lg bg-green-600 hover:bg-green-500 disabled:bg-gray-700 disabled:text-gray-500 font-semibold transition">
        {loading ? "Running Backtest..." : "Run Backtest"}
      </button>

      {error && (
        <div className="bg-red-900/40 border border-red-500 text-red-300 rounded-lg p-3 text-sm">{error}</div>
      )}

      {result && (
        <>
          {/* Equity Curve */}
          <div className="bg-gray-800 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-gray-400 mb-2">Equity Curve</h3>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={result.equityCurve}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="date" tick={{ fill: "#9ca3af", fontSize: 10 }} />
                <YAxis tick={{ fill: "#9ca3af", fontSize: 10 }} />
                <Tooltip contentStyle={{ backgroundColor: "#1f2937", border: "none", color: "#fff" }}
                  formatter={(v: number) => `$${v.toLocaleString()}`} />
                <Line type="monotone" dataKey="equity" stroke="#22c55e" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Metrics Table */}
          <div className="bg-gray-800 rounded-xl overflow-hidden">
            <h3 className="text-sm font-semibold text-gray-400 p-3 pb-0">Performance Metrics</h3>
            <table className="w-full text-sm">
              <tbody>
                {[
                  { label: "Sharpe Ratio", value: result.metrics.sharpe.toFixed(3), color: result.metrics.sharpe > 1 ? "text-green-400" : result.metrics.sharpe > 0 ? "text-yellow-400" : "text-red-400" },
                  { label: "Max Drawdown", value: `${(result.metrics.maxDrawdown * 100).toFixed(2)}%`, color: "text-red-400" },
                  { label: "Win Rate", value: `${(result.metrics.winRate * 100).toFixed(1)}%`, color: result.metrics.winRate > 0.5 ? "text-green-400" : "text-yellow-400" },
                  { label: "Total Return", value: `${(result.metrics.totalReturn * 100).toFixed(2)}%`, color: result.metrics.totalReturn > 0 ? "text-green-400" : "text-red-400" },
                  { label: "CAGR", value: `${(result.metrics.cagr * 100).toFixed(2)}%`, color: "text-cyan-400" },
                  { label: "Volatility", value: `${(result.metrics.volatility * 100).toFixed(2)}%`, color: "text-yellow-400" },
                  { label: "Total Trades", value: result.metrics.trades.toString(), color: "text-gray-300" },
                  { label: "Profit Factor", value: result.metrics.profitFactor.toFixed(2), color: result.metrics.profitFactor > 1 ? "text-green-400" : "text-red-400" },
                ].map((m) => (
                  <tr key={m.label} className="border-t border-gray-700/50 hover:bg-gray-700/30">
                    <td className="p-3 text-gray-400">{m.label}</td>
                    <td className={`p-3 text-right font-mono font-semibold ${m.color}`}>{m.value}</td>
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
