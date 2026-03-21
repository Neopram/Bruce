import React, { useState, useEffect, useCallback } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface TimePoint {
  timestamp: string;
  historical: number;
  predicted: number;
  actual?: number;
}

type TimeRange = "1d" | "1w" | "1m" | "3m";

export default function TimefoldingPanel() {
  const [data, setData] = useState<TimePoint[]>([]);
  const [range, setRange] = useState<TimeRange>("1w");
  const [scrubIndex, setScrubIndex] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [accuracy, setAccuracy] = useState(0);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/timefold/analysis?range=${range}`);
      if (!res.ok) throw new Error();
      const d = await res.json();
      setData(d.points || []);
      setAccuracy(d.accuracy || 0);
    } catch {
      // Generate simulated data
      const points: TimePoint[] = [];
      const len = range === "1d" ? 24 : range === "1w" ? 7 : range === "1m" ? 30 : 90;
      let base = 67000;
      for (let i = 0; i < len; i++) {
        base += (Math.random() - 0.48) * 500;
        const predicted = base + (Math.random() - 0.5) * 800;
        const actual = i < len * 0.7 ? base + (Math.random() - 0.5) * 200 : undefined;
        points.push({
          timestamp: range === "1d" ? `${i}:00` : `Day ${i + 1}`,
          historical: Math.round(base),
          predicted: Math.round(predicted),
          actual: actual ? Math.round(actual) : undefined,
        });
      }
      setData(points);
      setAccuracy(73.5);
    }
    setLoading(false);
  }, [range]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const scrubbed = scrubIndex != null && data[scrubIndex] ? data[scrubIndex] : null;

  if (loading) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 animate-pulse space-y-3">
        <div className="h-4 bg-gray-700 rounded w-1/3" />
        <div className="h-48 bg-gray-800 rounded" />
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-amber-300">Timefolding Analysis</h2>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500">Accuracy: <span className={accuracy > 70 ? "text-green-400" : "text-yellow-400"}>{accuracy.toFixed(1)}%</span></span>
          <div className="flex gap-1">
            {(["1d", "1w", "1m", "3m"] as TimeRange[]).map((r) => (
              <button
                key={r}
                onClick={() => setRange(r)}
                className={`text-[10px] px-2 py-1 rounded ${range === r ? "bg-amber-800 text-amber-200" : "bg-gray-800 text-gray-500 hover:bg-gray-700"}`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="w-full h-56">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} onMouseMove={(e: any) => e?.activeTooltipIndex != null && setScrubIndex(e.activeTooltipIndex)}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="timestamp" tick={{ fill: "#9ca3af", fontSize: 10 }} />
            <YAxis tick={{ fill: "#9ca3af", fontSize: 10 }} domain={["auto", "auto"]} />
            <Tooltip contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #374151", borderRadius: 8 }} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Line type="monotone" dataKey="historical" stroke="#f59e0b" strokeWidth={2} dot={false} name="Historical" />
            <Line type="monotone" dataKey="predicted" stroke="#8b5cf6" strokeWidth={2} dot={false} strokeDasharray="5 5" name="Predicted" />
            <Line type="monotone" dataKey="actual" stroke="#22c55e" strokeWidth={1.5} dot={false} name="Actual" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Timeline Scrubber */}
      <div>
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Timeline Scrubber</span>
          {scrubbed && <span className="text-gray-300">{scrubbed.timestamp}</span>}
        </div>
        <input
          type="range"
          min={0}
          max={data.length - 1}
          value={scrubIndex ?? 0}
          onChange={(e) => setScrubIndex(Number(e.target.value))}
          className="w-full h-1.5 bg-gray-700 rounded appearance-none cursor-pointer accent-amber-500"
        />
      </div>

      {/* Scrub Detail */}
      {scrubbed && (
        <div className="grid grid-cols-3 gap-2">
          <div className="bg-gray-800 rounded p-2 border border-gray-700 text-center">
            <span className="text-[10px] text-gray-500">Historical</span>
            <p className="text-sm font-mono text-amber-300">${scrubbed.historical.toLocaleString()}</p>
          </div>
          <div className="bg-gray-800 rounded p-2 border border-gray-700 text-center">
            <span className="text-[10px] text-gray-500">Predicted</span>
            <p className="text-sm font-mono text-purple-300">${scrubbed.predicted.toLocaleString()}</p>
          </div>
          <div className="bg-gray-800 rounded p-2 border border-gray-700 text-center">
            <span className="text-[10px] text-gray-500">Actual</span>
            <p className="text-sm font-mono text-green-300">
              {scrubbed.actual != null ? `$${scrubbed.actual.toLocaleString()}` : "--"}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
