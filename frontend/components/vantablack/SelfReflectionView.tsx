import React, { useState, useCallback, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import Badge from "@/components/ui/badge";
import Progress from "@/components/ui/progress";

interface ReflectionData {
  known: string[];
  unknown: string[];
  confidence: number;
  selfAssessment: string;
  improvements: string[];
  cognitiveMetrics: {
    selfAwareness: number;
    adaptability: number;
    reasoning: number;
    creativity: number;
    empathy: number;
  };
}

interface ReflectionHistoryEntry {
  id: string;
  timestamp: string;
  confidence: number;
  summary: string;
}

export default function SelfReflectionView() {
  const [reflection, setReflection] = useState<ReflectionData | null>(null);
  const [history, setHistory] = useState<ReflectionHistoryEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<"known" | "unknown" | null>(null);

  const fetchReflection = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/vantablack/self-reflection");
      if (!res.ok) throw new Error(`Failed (${res.status})`);
      const data = await res.json();
      const processed: ReflectionData = {
        known: data.known || [],
        unknown: data.unknown || [],
        confidence: data.confidence ?? 0.72,
        selfAssessment: data.selfAssessment || data.assessment || "System operating within expected cognitive parameters.",
        improvements: data.improvements || ["Optimize response latency", "Expand knowledge base"],
        cognitiveMetrics: data.cognitiveMetrics || {
          selfAwareness: 78,
          adaptability: 82,
          reasoning: 91,
          creativity: 67,
          empathy: 73,
        },
      };
      setReflection(processed);
      setHistory((prev) => [
        {
          id: `ref-${Date.now()}`,
          timestamp: new Date().toISOString(),
          confidence: processed.confidence,
          summary: processed.selfAssessment.slice(0, 80),
        },
        ...prev,
      ].slice(0, 10));
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <Card className="bg-gradient-to-br from-zinc-900 to-blue-950/20 border-blue-800/30">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-white">Cognitive Self-Reflection</h2>
          <button
            onClick={fetchReflection}
            disabled={loading}
            className="px-4 py-1.5 bg-blue-700 hover:bg-blue-600 rounded-lg text-sm text-white transition-colors disabled:opacity-50"
          >
            {loading ? "Reflecting..." : "Reflect"}
          </button>
        </div>

        {error && (
          <div className="mb-4 p-2 rounded-lg bg-red-900/30 border border-red-800/50 text-red-400 text-sm">
            {error}
          </div>
        )}

        {reflection ? (
          <div className="space-y-4">
            {/* Self Assessment */}
            <div className="p-3 bg-blue-900/20 border border-blue-800/30 rounded-lg">
              <p className="text-sm text-blue-200 italic">{reflection.selfAssessment}</p>
              <div className="flex items-center gap-2 mt-2">
                <span className="text-xs text-zinc-400">Confidence:</span>
                <Progress value={reflection.confidence * 100} variant="info" size="sm" className="flex-1 max-w-32" />
                <span className="text-xs font-mono text-blue-400">{(reflection.confidence * 100).toFixed(0)}%</span>
              </div>
            </div>

            {/* Cognitive Metrics */}
            <div>
              <h3 className="text-sm font-medium text-zinc-300 mb-2">Cognitive Metrics</h3>
              <div className="space-y-2">
                {Object.entries(reflection.cognitiveMetrics).map(([key, value]) => (
                  <div key={key}>
                    <div className="flex justify-between text-xs mb-0.5">
                      <span className="text-zinc-400 capitalize">{key.replace(/([A-Z])/g, " $1").trim()}</span>
                      <span className="text-zinc-500">{value}%</span>
                    </div>
                    <Progress
                      value={value}
                      variant={value >= 80 ? "success" : value >= 60 ? "info" : "warning"}
                      size="sm"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Known / Unknown */}
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setExpanded(expanded === "known" ? null : "known")}
                className="text-left p-3 bg-emerald-900/20 border border-emerald-800/30 rounded-lg hover:bg-emerald-900/30 transition-colors"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-emerald-400">Known</span>
                  <Badge variant="success" size="sm">{reflection.known.length}</Badge>
                </div>
                {expanded === "known" && (
                  <ul className="mt-2 space-y-1">
                    {reflection.known.map((k, i) => (
                      <li key={i} className="text-xs text-emerald-200">{k}</li>
                    ))}
                  </ul>
                )}
              </button>
              <button
                onClick={() => setExpanded(expanded === "unknown" ? null : "unknown")}
                className="text-left p-3 bg-amber-900/20 border border-amber-800/30 rounded-lg hover:bg-amber-900/30 transition-colors"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-amber-400">Unknown</span>
                  <Badge variant="warning" size="sm">{reflection.unknown.length}</Badge>
                </div>
                {expanded === "unknown" && (
                  <ul className="mt-2 space-y-1">
                    {reflection.unknown.map((u, i) => (
                      <li key={i} className="text-xs text-amber-200">{u}</li>
                    ))}
                  </ul>
                )}
              </button>
            </div>

            {/* Improvements */}
            {reflection.improvements.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-zinc-300 mb-2">Suggested Improvements</h3>
                <ul className="space-y-1">
                  {reflection.improvements.map((imp, i) => (
                    <li key={i} className="flex items-center gap-2 text-xs text-zinc-400">
                      <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
                      {imp}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* History */}
            {history.length > 1 && (
              <div>
                <h3 className="text-xs font-medium text-zinc-500 mb-1">Reflection History</h3>
                <div className="flex gap-1 flex-wrap">
                  {history.slice(0, 5).map((h) => (
                    <span key={h.id} className="px-2 py-0.5 text-xs bg-zinc-800/50 rounded text-zinc-500">
                      {(h.confidence * 100).toFixed(0)}% @ {new Date(h.timestamp).toLocaleTimeString()}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="py-8 text-center text-zinc-500">
            <p>No reflection data available.</p>
            <p className="text-xs mt-1">Click "Reflect" to initiate cognitive self-evaluation.</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
