import React, { useState } from "react";
import {
  ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  PieChart, Pie, Cell,
} from "recharts";

interface Asset {
  name: string;
  weight: number;
}

interface OptResult {
  frontier: { risk: number; return_: number }[];
  allocation: { name: string; weight: number }[];
  sharpe: number;
  expectedReturn: number;
  volatility: number;
}

const PIE_COLORS = ["#06b6d4", "#8b5cf6", "#22c55e", "#f59e0b", "#ef4444", "#ec4899", "#14b8a6", "#f97316"];

export default function PortfolioOptimizerPanel() {
  const [assets, setAssets] = useState<Asset[]>([
    { name: "BTC", weight: 30 },
    { name: "ETH", weight: 25 },
    { name: "SOL", weight: 20 },
    { name: "AAPL", weight: 15 },
    { name: "BONDS", weight: 10 },
  ]);
  const [result, setResult] = useState<OptResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateAsset = (idx: number, field: keyof Asset, value: string) => {
    const next = [...assets];
    if (field === "weight") next[idx].weight = Number(value) || 0;
    else next[idx].name = value;
    setAssets(next);
  };

  const addAsset = () => setAssets([...assets, { name: "", weight: 0 }]);
  const removeAsset = (idx: number) => setAssets(assets.filter((_, i) => i !== idx));

  const totalWeight = assets.reduce((s, a) => s + a.weight, 0);

  const optimize = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/v1/portfolio/optimize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ assets }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setResult(await res.json());
    } catch (e: any) {
      setError(e.message ?? "Optimization failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gray-900 text-white rounded-2xl shadow-lg p-6 space-y-5">
      <h2 className="text-xl font-bold">Portfolio Optimizer</h2>

      {/* Asset inputs */}
      <div className="space-y-2">
        {assets.map((a, i) => (
          <div key={i} className="flex gap-2 items-center">
            <input value={a.name} onChange={(e) => updateAsset(i, "name", e.target.value)}
              placeholder="Asset" className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-cyan-500" />
            <input type="number" value={a.weight} onChange={(e) => updateAsset(i, "weight", e.target.value)}
              className="w-20 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-right focus:outline-none focus:border-cyan-500" />
            <span className="text-gray-500 text-sm">%</span>
            <button onClick={() => removeAsset(i)} className="text-red-400 hover:text-red-300 text-sm px-2">X</button>
          </div>
        ))}
        <div className="flex justify-between items-center">
          <button onClick={addAsset} className="text-sm text-cyan-400 hover:text-cyan-300">+ Add Asset</button>
          <span className={`text-sm ${totalWeight === 100 ? "text-green-400" : "text-yellow-400"}`}>
            Total: {totalWeight}%
          </span>
        </div>
      </div>

      {/* Optimize button */}
      <button onClick={optimize} disabled={loading || assets.length < 2}
        className="w-full py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:bg-gray-700 disabled:text-gray-500 font-semibold transition">
        {loading ? "Optimizing..." : "Run Markowitz Optimization"}
      </button>

      {error && (
        <div className="bg-red-900/40 border border-red-500 text-red-300 rounded-lg p-3 text-sm">{error}</div>
      )}

      {result && (
        <>
          {/* Metrics */}
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "Sharpe Ratio", value: result.sharpe.toFixed(3), color: "text-cyan-400" },
              { label: "Exp. Return", value: `${(result.expectedReturn * 100).toFixed(2)}%`, color: "text-green-400" },
              { label: "Volatility", value: `${(result.volatility * 100).toFixed(2)}%`, color: "text-yellow-400" },
            ].map((m) => (
              <div key={m.label} className="bg-gray-800 rounded-xl p-3 text-center">
                <p className="text-xs text-gray-500">{m.label}</p>
                <p className={`text-xl font-mono font-bold ${m.color}`}>{m.value}</p>
              </div>
            ))}
          </div>

          {/* Efficient Frontier */}
          <div className="bg-gray-800 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-gray-400 mb-2">Efficient Frontier</h3>
            <ResponsiveContainer width="100%" height={200}>
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="risk" name="Risk" tick={{ fill: "#9ca3af", fontSize: 10 }} label={{ value: "Risk", fill: "#9ca3af", fontSize: 11, position: "bottom" }} />
                <YAxis dataKey="return_" name="Return" tick={{ fill: "#9ca3af", fontSize: 10 }} label={{ value: "Return", fill: "#9ca3af", fontSize: 11, angle: -90, position: "insideLeft" }} />
                <Tooltip contentStyle={{ backgroundColor: "#1f2937", border: "none", color: "#fff" }}
                  formatter={(val: number) => `${(val * 100).toFixed(2)}%`} />
                <Scatter data={result.frontier} fill="#06b6d4" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>

          {/* Optimal Allocation Pie */}
          <div className="bg-gray-800 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-gray-400 mb-2">Optimal Allocation</h3>
            <div className="flex items-center gap-4">
              <ResponsiveContainer width="50%" height={180}>
                <PieChart>
                  <Pie data={result.allocation} dataKey="weight" nameKey="name" cx="50%" cy="50%"
                    outerRadius={70} innerRadius={35} paddingAngle={2}>
                    {result.allocation.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: "#1f2937", border: "none", color: "#fff" }}
                    formatter={(val: number) => `${val.toFixed(1)}%`} />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex-1 space-y-1">
                {result.allocation.map((a, i) => (
                  <div key={a.name} className="flex items-center gap-2 text-sm">
                    <span className="w-3 h-3 rounded-full" style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }} />
                    <span className="flex-1">{a.name}</span>
                    <span className="font-mono text-gray-300">{a.weight.toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
