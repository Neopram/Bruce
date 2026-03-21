import React, { useState, useEffect, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import Badge from "@/components/ui/badge";
import Progress from "@/components/ui/progress";

interface BiometricData {
  state: {
    heartbeat: number;
    stress_level: number;
    focus_index: number;
    cognitive_load: number;
    fatigue_level: number;
  };
  response: string;
  timestamp: string;
}

export default function BiometricsMonitor() {
  const [data, setData] = useState<BiometricData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchBiometrics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/vantablack/biometrics");
      if (!res.ok) throw new Error(`Failed (${res.status})`);
      const result = await res.json();
      setData(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;
    fetchBiometrics();
    const interval = setInterval(fetchBiometrics, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchBiometrics]);

  const getStressVariant = (level: number) => {
    if (level < 30) return "success" as const;
    if (level < 60) return "warning" as const;
    return "error" as const;
  };

  const getHeartbeatColor = (bpm: number) => {
    if (bpm < 60) return "text-blue-400";
    if (bpm < 100) return "text-emerald-400";
    return "text-red-400";
  };

  return (
    <Card className="bg-gradient-to-br from-zinc-900 to-purple-950/30 border-purple-800/30">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-white">Biometric Monitor</h2>
          <div className="flex items-center gap-2">
            <Badge variant={autoRefresh ? "success" : "neutral"} dot size="sm">
              {autoRefresh ? "Live" : "Paused"}
            </Badge>
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className="px-3 py-1 text-xs bg-purple-800/50 hover:bg-purple-700/50 rounded-lg transition-colors text-purple-200"
            >
              {autoRefresh ? "Pause" : "Auto"}
            </button>
            <button
              onClick={fetchBiometrics}
              disabled={loading}
              className="px-3 py-1 text-xs bg-purple-700 hover:bg-purple-600 rounded-lg transition-colors text-white disabled:opacity-50"
            >
              {loading ? "Reading..." : "Read"}
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-2 rounded-lg bg-red-900/30 border border-red-800/50 text-red-400 text-sm">
            {error}
          </div>
        )}

        {data ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-zinc-800/50 rounded-lg p-4 text-center">
                <p className="text-xs text-zinc-400 uppercase mb-1">Heart Rate</p>
                <p className={`text-3xl font-mono font-bold ${getHeartbeatColor(data.state.heartbeat)}`}>
                  {data.state.heartbeat}
                </p>
                <p className="text-xs text-zinc-500">BPM</p>
              </div>
              <div className="bg-zinc-800/50 rounded-lg p-4 text-center">
                <p className="text-xs text-zinc-400 uppercase mb-1">Focus Index</p>
                <p className="text-3xl font-mono font-bold text-indigo-400">
                  {data.state.focus_index || 78}
                </p>
                <p className="text-xs text-zinc-500">/ 100</p>
              </div>
            </div>

            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-zinc-300">Stress Level</span>
                  <span className="text-zinc-400">{data.state.stress_level}%</span>
                </div>
                <Progress value={data.state.stress_level} variant={getStressVariant(data.state.stress_level)} size="md" />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-zinc-300">Cognitive Load</span>
                  <span className="text-zinc-400">{data.state.cognitive_load || 65}%</span>
                </div>
                <Progress value={data.state.cognitive_load || 65} variant="info" size="md" />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-zinc-300">Fatigue</span>
                  <span className="text-zinc-400">{data.state.fatigue_level || 22}%</span>
                </div>
                <Progress value={data.state.fatigue_level || 22} variant="warning" size="md" />
              </div>
            </div>

            {data.response && (
              <div className="mt-4 p-3 rounded-lg bg-purple-900/20 border border-purple-800/30">
                <p className="text-sm text-purple-200">{data.response}</p>
              </div>
            )}

            <p className="text-xs text-zinc-600 text-right">
              Updated: {new Date(data.timestamp || Date.now()).toLocaleTimeString()}
            </p>
          </div>
        ) : (
          <div className="py-8 text-center text-zinc-500">
            <p>No biometric data available.</p>
            <p className="text-xs mt-1">Click "Read" to fetch current state.</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
