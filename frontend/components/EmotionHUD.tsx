import React, { useEffect, useState, useCallback } from "react";
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Radar, ResponsiveContainer, Tooltip,
} from "recharts";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface EmotionState {
  joy: number;
  anger: number;
  fear: number;
  sadness: number;
  surprise: number;
  disgust: number;
  trust: number;
  anticipation: number;
  dominant: string;
  intensity: number;
}

const EMOTION_COLORS: Record<string, string> = {
  joy: "#facc15",
  anger: "#ef4444",
  fear: "#a855f7",
  sadness: "#3b82f6",
  surprise: "#f97316",
  disgust: "#22c55e",
  trust: "#06b6d4",
  anticipation: "#ec4899",
};

export default function EmotionHUD() {
  const [emotion, setEmotion] = useState<EmotionState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEmotion = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/bruce-api/emotion/state/default`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setEmotion({
        joy: data.joy ?? 0.5,
        anger: data.anger ?? 0.1,
        fear: data.fear ?? 0.2,
        sadness: data.sadness ?? 0.1,
        surprise: data.surprise ?? 0.3,
        disgust: data.disgust ?? 0.05,
        trust: data.trust ?? 0.7,
        anticipation: data.anticipation ?? 0.6,
        dominant: data.dominant ?? "neutral",
        intensity: data.intensity ?? 0.5,
      });
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to fetch emotion state");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEmotion();
    const interval = setInterval(fetchEmotion, 3000);
    return () => clearInterval(interval);
  }, [fetchEmotion]);

  if (loading) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 animate-pulse">
        <div className="h-4 bg-gray-700 rounded w-1/3 mb-4" />
        <div className="h-48 bg-gray-800 rounded" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-900 border border-red-800 rounded-xl p-6">
        <h2 className="text-lg font-bold text-red-400 mb-2">Emotion HUD</h2>
        <p className="text-red-300 text-sm">{error}</p>
        <button onClick={fetchEmotion} className="mt-3 px-3 py-1 bg-red-700 hover:bg-red-600 text-white text-sm rounded">
          Retry
        </button>
      </div>
    );
  }

  const radarData = emotion
    ? Object.entries(EMOTION_COLORS).map(([key]) => ({
        emotion: key.charAt(0).toUpperCase() + key.slice(1),
        value: (emotion as any)[key] ?? 0,
      }))
    : [];

  const dominantColor = emotion ? EMOTION_COLORS[emotion.dominant] || "#8b5cf6" : "#8b5cf6";

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-purple-300">Emotion HUD</h2>
        <div className="flex items-center gap-2">
          <span
            className="inline-block w-3 h-3 rounded-full animate-pulse"
            style={{ backgroundColor: dominantColor }}
          />
          <span className="text-sm font-medium capitalize" style={{ color: dominantColor }}>
            {emotion?.dominant}
          </span>
        </div>
      </div>

      <div className="w-full h-56">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={radarData} outerRadius="75%">
            <PolarGrid stroke="#374151" />
            <PolarAngleAxis dataKey="emotion" tick={{ fill: "#9ca3af", fontSize: 11 }} />
            <PolarRadiusAxis domain={[0, 1]} tick={false} axisLine={false} />
            <Tooltip
              contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #374151", borderRadius: 8 }}
              labelStyle={{ color: "#e5e7eb" }}
              itemStyle={{ color: "#c084fc" }}
            />
            <Radar
              name="Emotion"
              dataKey="value"
              stroke="#8b5cf6"
              fill="#8b5cf6"
              fillOpacity={0.3}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-between text-xs text-gray-400">
        <span>Intensity: {((emotion?.intensity ?? 0) * 100).toFixed(0)}%</span>
        <span className="text-green-400">LIVE</span>
      </div>
    </div>
  );
}
