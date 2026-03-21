import React, { useState, useEffect, useCallback } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";

interface IndicatorData {
  rsi: number;
  macd: { histogram: number[] };
  bollinger: { upper: number; middle: number; lower: number };
  sma: { sma20: number; sma50: number; sma200: number };
}

const RSI_COLORS = (v: number) =>
  v <= 30 ? "#22c55e" : v >= 70 ? "#ef4444" : "#facc15";

export default function IndicatorsPanel() {
  const [data, setData] = useState<IndicatorData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchIndicators = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/v1/indicators");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
    } catch (e: any) {
      setError(e.message ?? "Failed to load indicators");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchIndicators(); }, [fetchIndicators]);

  const macdData = (data?.macd?.histogram ?? []).map((v, i) => ({
    name: `${i + 1}`,
    value: v,
  }));

  const rsiAngle = data ? (data.rsi / 100) * 180 : 0;

  return (
    <div className="bg-gray-900 text-white rounded-2xl shadow-lg p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Technical Indicators</h2>
        <button
          onClick={fetchIndicators}
          className="px-3 py-1 text-sm rounded bg-gray-700 hover:bg-gray-600 transition"
        >
          Refresh
        </button>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin h-8 w-8 border-4 border-cyan-400 border-t-transparent rounded-full" />
        </div>
      )}

      {error && (
        <div className="bg-red-900/40 border border-red-500 text-red-300 rounded-lg p-4">
          <p className="font-semibold">Error</p>
          <p className="text-sm">{error}</p>
          <button onClick={fetchIndicators} className="mt-2 text-sm underline hover:text-red-200">
            Retry
          </button>
        </div>
      )}

      {!loading && !error && data && (
        <>
          {/* RSI Gauge */}
          <div className="bg-gray-800 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-gray-400 mb-3">RSI (14)</h3>
            <div className="flex items-center gap-6">
              <svg viewBox="0 0 120 70" className="w-32 h-20">
                <path d="M10,60 A50,50 0 0,1 110,60" fill="none" stroke="#374151" strokeWidth="8" strokeLinecap="round" />
                <path d="M10,60 A50,50 0 0,1 110,60" fill="none" stroke="url(#rsiGrad)" strokeWidth="8" strokeLinecap="round"
                  strokeDasharray={`${(rsiAngle / 180) * 157} 157`} />
                <defs>
                  <linearGradient id="rsiGrad" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#22c55e" />
                    <stop offset="50%" stopColor="#facc15" />
                    <stop offset="100%" stopColor="#ef4444" />
                  </linearGradient>
                </defs>
                <text x="60" y="55" textAnchor="middle" fill="white" fontSize="16" fontWeight="bold">
                  {data.rsi.toFixed(1)}
                </text>
              </svg>
              <div className="text-sm space-y-1">
                <p style={{ color: RSI_COLORS(data.rsi) }}>
                  {data.rsi <= 30 ? "Oversold" : data.rsi >= 70 ? "Overbought" : "Neutral"}
                </p>
                <p className="text-gray-400">Range: 0 - 100</p>
              </div>
            </div>
          </div>

          {/* MACD Histogram */}
          <div className="bg-gray-800 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-gray-400 mb-3">MACD Histogram</h3>
            <ResponsiveContainer width="100%" height={120}>
              <BarChart data={macdData}>
                <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 10 }} />
                <YAxis tick={{ fill: "#9ca3af", fontSize: 10 }} />
                <Tooltip contentStyle={{ backgroundColor: "#1f2937", border: "none", color: "#fff" }} />
                <Bar dataKey="value">
                  {macdData.map((entry, idx) => (
                    <Cell key={idx} fill={entry.value >= 0 ? "#22c55e" : "#ef4444"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Bollinger Bands */}
          <div className="bg-gray-800 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-gray-400 mb-3">Bollinger Bands</h3>
            <div className="grid grid-cols-3 gap-3 text-center">
              <div>
                <p className="text-xs text-gray-500">Upper</p>
                <p className="text-lg font-mono text-red-400">{data.bollinger.upper.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Middle</p>
                <p className="text-lg font-mono text-yellow-400">{data.bollinger.middle.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Lower</p>
                <p className="text-lg font-mono text-green-400">{data.bollinger.lower.toFixed(2)}</p>
              </div>
            </div>
            <div className="mt-3 h-2 rounded-full bg-gray-700 relative overflow-hidden">
              <div className="absolute inset-y-0 bg-gradient-to-r from-green-500 via-yellow-400 to-red-500 rounded-full"
                style={{ left: "10%", right: "10%" }} />
            </div>
          </div>

          {/* SMA Values */}
          <div className="bg-gray-800 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-gray-400 mb-3">Simple Moving Averages</h3>
            <div className="grid grid-cols-3 gap-3 text-center">
              {[
                { label: "SMA 20", value: data.sma.sma20, color: "text-cyan-400" },
                { label: "SMA 50", value: data.sma.sma50, color: "text-blue-400" },
                { label: "SMA 200", value: data.sma.sma200, color: "text-purple-400" },
              ].map((s) => (
                <div key={s.label}>
                  <p className="text-xs text-gray-500">{s.label}</p>
                  <p className={`text-lg font-mono ${s.color}`}>{s.value.toFixed(2)}</p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
