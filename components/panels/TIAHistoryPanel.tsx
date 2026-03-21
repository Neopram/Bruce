import React, { useEffect, useState, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import Badge from "@/components/ui/badge";
import axios from "axios";

interface TIAEntry {
  id: string;
  timestamp: string;
  command: string;
  output: string;
  status: "success" | "error" | "warning" | "info";
  duration?: number;
  agent?: string;
}

const TIAHistoryPanel = () => {
  const [history, setHistory] = useState<TIAEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("all");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const pageSize = 10;

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get("/api/tia-agent/history");
      const data = Array.isArray(res.data) ? res.data : res.data?.entries || [];
      setHistory(
        data.map((entry: any, idx: number) => ({
          id: entry.id || `tia-${idx}`,
          timestamp: entry.timestamp || new Date().toISOString(),
          command: entry.command || entry.task || "Unknown",
          output: entry.output || entry.result || "",
          status: entry.status || "info",
          duration: entry.duration,
          agent: entry.agent,
        }))
      );
    } catch (err: any) {
      setError(err.message || "Failed to load TIA history");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const statusVariant = (s: string) => {
    const map: Record<string, "success" | "error" | "warning" | "info"> = {
      success: "success", error: "error", warning: "warning", info: "info",
    };
    return map[s] || "info";
  };

  const filtered = filter === "all"
    ? history
    : history.filter(e => e.status === filter);

  const paginated = filtered.slice(page * pageSize, (page + 1) * pageSize);
  const totalPages = Math.ceil(filtered.length / pageSize);

  const statusCounts = {
    all: history.length,
    success: history.filter(e => e.status === "success").length,
    error: history.filter(e => e.status === "error").length,
    warning: history.filter(e => e.status === "warning").length,
  };

  return (
    <Card className="bg-zinc-900 border-zinc-800">
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">TIA Agent History</h2>
          <button
            onClick={fetchHistory}
            disabled={loading}
            className="px-3 py-1 text-xs bg-zinc-700 hover:bg-zinc-600 rounded-lg text-zinc-300 transition-colors disabled:opacity-50"
          >
            {loading ? "Loading..." : "Refresh"}
          </button>
        </div>

        {error && (
          <div className="mb-3 p-2 rounded-lg bg-red-900/30 border border-red-800/50 text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Status Filters */}
        <div className="flex gap-2 mb-4">
          {(["all", "success", "error", "warning"] as const).map(f => (
            <button
              key={f}
              onClick={() => { setFilter(f); setPage(0); }}
              className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
                filter === f
                  ? "bg-indigo-800/30 border-indigo-600/50 text-indigo-300"
                  : "bg-zinc-800/50 border-zinc-700/50 text-zinc-400"
              }`}
            >
              {f} ({statusCounts[f as keyof typeof statusCounts] ?? 0})
            </button>
          ))}
        </div>

        {/* Entries */}
        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          {paginated.length === 0 ? (
            <p className="text-center text-zinc-500 py-6 text-sm">
              {loading ? "Loading history..." : "No TIA entries found."}
            </p>
          ) : (
            paginated.map((entry) => (
              <div key={entry.id} className="rounded-lg bg-zinc-800/50 border border-zinc-700/50 overflow-hidden">
                <button
                  onClick={() => setExpandedId(expandedId === entry.id ? null : entry.id)}
                  className="w-full p-3 text-left flex items-start gap-3 hover:bg-zinc-800/80 transition-colors"
                >
                  <Badge variant={statusVariant(entry.status)} size="sm" className="mt-0.5">
                    {entry.status}
                  </Badge>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-zinc-200 font-medium truncate">{entry.command}</p>
                    <div className="flex items-center gap-3 mt-0.5 text-xs text-zinc-500">
                      <span>{new Date(entry.timestamp).toLocaleString()}</span>
                      {entry.duration != null && <span>{entry.duration}ms</span>}
                      {entry.agent && <span>{entry.agent}</span>}
                    </div>
                  </div>
                  <svg
                    className={`w-4 h-4 text-zinc-500 transition-transform flex-shrink-0 ${
                      expandedId === entry.id ? "rotate-180" : ""
                    }`}
                    fill="none" stroke="currentColor" viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {expandedId === entry.id && entry.output && (
                  <div className="px-3 pb-3">
                    <pre className="text-xs font-mono text-zinc-400 bg-zinc-900 p-3 rounded overflow-x-auto max-h-40">
                      {entry.output}
                    </pre>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-3 text-xs text-zinc-500">
            <span>
              Showing {page * pageSize + 1}-{Math.min((page + 1) * pageSize, filtered.length)} of {filtered.length}
            </span>
            <div className="flex gap-1">
              <button
                onClick={() => setPage(p => Math.max(0, p - 1))}
                disabled={page === 0}
                className="px-2 py-1 rounded bg-zinc-800 hover:bg-zinc-700 disabled:opacity-30"
              >
                Prev
              </button>
              <button
                onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="px-2 py-1 rounded bg-zinc-800 hover:bg-zinc-700 disabled:opacity-30"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default TIAHistoryPanel;
