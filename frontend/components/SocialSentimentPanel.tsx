import React, { useState, useEffect, useCallback } from "react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";

interface SentimentData {
  fearGreed: number;
  trending: { topic: string; sentiment: number; volume: number }[];
  sources: { name: string; positive: number; negative: number; neutral: number }[];
  trend: { date: string; sentiment: number }[];
}

const fearGreedColor = (v: number) =>
  v <= 25 ? "#ef4444" : v <= 45 ? "#f59e0b" : v <= 55 ? "#9ca3af" : v <= 75 ? "#22c55e" : "#06b6d4";
const fearGreedLabel = (v: number) =>
  v <= 25 ? "Extreme Fear" : v <= 45 ? "Fear" : v <= 55 ? "Neutral" : v <= 75 ? "Greed" : "Extreme Greed";

export default function SocialSentimentPanel() {
  const [data, setData] = useState<SentimentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [symbol, setSymbol] = useState("BTC");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/sentiment/${symbol}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setData(await res.json());
    } catch (e: any) {
      setError(e.message ?? "Failed to load sentiment");
    } finally {
      setLoading(false);
    }
  }, [symbol]);

  useEffect(() => { fetchData(); }, [fetchData]);

  return (
    <div className="bg-gray-900 text-white rounded-2xl shadow-lg p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Social Sentiment</h2>
        <div className="flex items-center gap-2">
          <input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            className="w-20 bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-center focus:outline-none focus:border-cyan-500" />
          <button onClick={fetchData} className="px-3 py-1.5 text-sm rounded bg-gray-700 hover:bg-gray-600 transition">
            Refresh
          </button>
        </div>
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
        </div>
      )}

      {!loading && !error && data && (
        <>
          {/* Fear & Greed Gauge */}
          <div className="bg-gray-800 rounded-xl p-4 text-center">
            <h3 className="text-sm text-gray-400 mb-2">Fear &amp; Greed Index</h3>
            <svg viewBox="0 0 120 70" className="w-40 h-24 mx-auto">
              <path d="M10,60 A50,50 0 0,1 110,60" fill="none" stroke="#374151" strokeWidth="8" strokeLinecap="round" />
              <path d="M10,60 A50,50 0 0,1 110,60" fill="none" stroke={fearGreedColor(data.fearGreed)} strokeWidth="8" strokeLinecap="round"
                strokeDasharray={`${(data.fearGreed / 100) * 157} 157`} />
              <text x="60" y="52" textAnchor="middle" fill="white" fontSize="18" fontWeight="bold">{data.fearGreed}</text>
            </svg>
            <p className="text-sm font-semibold mt-1" style={{ color: fearGreedColor(data.fearGreed) }}>
              {fearGreedLabel(data.fearGreed)}
            </p>
          </div>

          {/* Trending Topics */}
          <div className="bg-gray-800 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-gray-400 mb-2">Trending Topics</h3>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {data.trending.map((t, i) => (
                <div key={i} className="flex items-center justify-between text-sm">
                  <span className="truncate flex-1">{t.topic}</span>
                  <span className={`font-mono ml-2 ${t.sentiment > 0 ? "text-green-400" : t.sentiment < 0 ? "text-red-400" : "text-gray-400"}`}>
                    {t.sentiment > 0 ? "+" : ""}{t.sentiment.toFixed(2)}
                  </span>
                  <span className="text-gray-600 text-xs ml-2">{t.volume.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Source Breakdown */}
          <div className="bg-gray-800 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-gray-400 mb-2">Source Breakdown</h3>
            <div className="space-y-2">
              {data.sources.map((s) => {
                const total = s.positive + s.negative + s.neutral;
                return (
                  <div key={s.name}>
                    <div className="flex justify-between text-sm mb-1">
                      <span>{s.name}</span>
                      <span className="text-gray-500">{total} mentions</span>
                    </div>
                    <div className="flex h-2 rounded-full overflow-hidden">
                      <div className="bg-green-500" style={{ width: `${(s.positive / total) * 100}%` }} />
                      <div className="bg-gray-500" style={{ width: `${(s.neutral / total) * 100}%` }} />
                      <div className="bg-red-500" style={{ width: `${(s.negative / total) * 100}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="flex gap-4 mt-2 text-xs text-gray-500 justify-center">
              <span className="flex items-center gap-1"><span className="w-2 h-2 bg-green-500 rounded-full" /> Positive</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 bg-gray-500 rounded-full" /> Neutral</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 bg-red-500 rounded-full" /> Negative</span>
            </div>
          </div>

          {/* Sentiment Trend Chart */}
          <div className="bg-gray-800 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-gray-400 mb-2">Sentiment Trend</h3>
            <ResponsiveContainer width="100%" height={150}>
              <AreaChart data={data.trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="date" tick={{ fill: "#9ca3af", fontSize: 10 }} />
                <YAxis tick={{ fill: "#9ca3af", fontSize: 10 }} domain={[-1, 1]} />
                <Tooltip contentStyle={{ backgroundColor: "#1f2937", border: "none", color: "#fff" }} />
                <Area type="monotone" dataKey="sentiment" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.15} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}
