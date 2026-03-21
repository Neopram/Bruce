import React, { useEffect, useState, useCallback } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from "recharts";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface EmotionSnapshot {
  timestamp: string;
  joy: number;
  anger: number;
  fear: number;
  sadness: number;
  trust: number;
}

interface EmotionDistribution {
  name: string;
  value: number;
}

const COLORS = ["#facc15", "#ef4444", "#a855f7", "#3b82f6", "#06b6d4", "#22c55e"];

const moodEmoji: Record<string, string> = {
  curioso: "?",
  relajado: "~",
  estresado: "!",
  euforico: "^",
  triste: "v",
  enfocado: ">",
};

export default function EmotionDashboard() {
  const [trend, setTrend] = useState<EmotionSnapshot[]>([]);
  const [distribution, setDistribution] = useState<EmotionDistribution[]>([]);
  const [correlation, setCorrelation] = useState<{ emotion: string; pnl: number }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [trendRes, distRes] = await Promise.allSettled([
        fetch(`${API_URL}/bruce-api/emotion/trend/default`),
        fetch(`${API_URL}/bruce-api/emotion/distribution/default`),
      ]);

      const trendData = trendRes.status === "fulfilled" && trendRes.value.ok
        ? await trendRes.value.json()
        : null;
      const distData = distRes.status === "fulfilled" && distRes.value.ok
        ? await distRes.value.json()
        : null;

      if (trendData?.history) {
        setTrend(trendData.history.slice(-20));
      } else {
        setTrend(
          Array.from({ length: 12 }, (_, i) => ({
            timestamp: `${i * 2}h`,
            joy: Math.random() * 0.8 + 0.1,
            anger: Math.random() * 0.3,
            fear: Math.random() * 0.4,
            sadness: Math.random() * 0.3,
            trust: Math.random() * 0.7 + 0.2,
          }))
        );
      }

      if (distData?.distribution) {
        setDistribution(distData.distribution);
      } else {
        setDistribution([
          { name: "Joy", value: 35 },
          { name: "Trust", value: 25 },
          { name: "Anticipation", value: 15 },
          { name: "Fear", value: 10 },
          { name: "Sadness", value: 8 },
          { name: "Anger", value: 7 },
        ]);
      }

      setCorrelation([
        { emotion: "Joy", pnl: 2.4 },
        { emotion: "Fear", pnl: -1.8 },
        { emotion: "Trust", pnl: 1.2 },
        { emotion: "Anger", pnl: -3.1 },
        { emotion: "Sadness", pnl: -0.5 },
      ]);

      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to fetch emotion data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 animate-pulse space-y-4">
        <div className="h-4 bg-gray-700 rounded w-1/3" />
        <div className="h-40 bg-gray-800 rounded" />
        <div className="h-40 bg-gray-800 rounded" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-900 border border-red-800 rounded-xl p-6">
        <h2 className="text-lg font-bold text-red-400">Emotion Dashboard</h2>
        <p className="text-red-300 text-sm mt-2">{error}</p>
        <button onClick={fetchData} className="mt-3 px-3 py-1 bg-red-700 hover:bg-red-600 text-white text-sm rounded">Retry</button>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-6">
      <h2 className="text-lg font-bold text-purple-300">Emotion Dashboard</h2>

      {/* Emotion Trend */}
      <div>
        <h3 className="text-sm font-semibold text-gray-400 mb-2">Emotion Trend</h3>
        <div className="w-full h-48">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="timestamp" tick={{ fill: "#9ca3af", fontSize: 10 }} />
              <YAxis domain={[0, 1]} tick={{ fill: "#9ca3af", fontSize: 10 }} />
              <Tooltip contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #374151", borderRadius: 8 }} />
              <Line type="monotone" dataKey="joy" stroke="#facc15" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="anger" stroke="#ef4444" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="fear" stroke="#a855f7" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="trust" stroke="#06b6d4" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Distribution + Correlation */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <h3 className="text-sm font-semibold text-gray-400 mb-2">Emotion Distribution</h3>
          <div className="w-full h-44">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={distribution} cx="50%" cy="50%" outerRadius={60} dataKey="value" label={({ name }) => name}>
                  {distribution.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #374151", borderRadius: 8 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-gray-400 mb-2">Emotion vs Trading PnL</h3>
          <div className="space-y-2">
            {correlation.map((c) => (
              <div key={c.emotion} className="flex items-center justify-between text-sm">
                <span className="text-gray-300">{c.emotion}</span>
                <span className={c.pnl >= 0 ? "text-green-400" : "text-red-400"}>
                  {c.pnl >= 0 ? "+" : ""}{c.pnl.toFixed(1)}%
                </span>
                <div className="w-24 h-2 bg-gray-700 rounded overflow-hidden">
                  <div
                    className={`h-full rounded ${c.pnl >= 0 ? "bg-green-500" : "bg-red-500"}`}
                    style={{ width: `${Math.min(Math.abs(c.pnl) * 15, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
