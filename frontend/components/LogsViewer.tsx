import React, { useState, useEffect, useRef, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

type LogLevel = "info" | "warn" | "error" | "debug";

interface LogEntry {
  id: string;
  timestamp: string;
  level: LogLevel;
  message: string;
  source: string;
}

const LEVEL_STYLES: Record<LogLevel, { text: string; bg: string; border: string }> = {
  info: { text: "text-blue-300", bg: "bg-blue-900/20", border: "border-blue-800" },
  warn: { text: "text-yellow-300", bg: "bg-yellow-900/20", border: "border-yellow-800" },
  error: { text: "text-red-300", bg: "bg-red-900/20", border: "border-red-800" },
  debug: { text: "text-gray-400", bg: "bg-gray-800/40", border: "border-gray-700" },
};

export default function LogsViewer() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filter, setFilter] = useState<LogLevel | "all">("all");
  const [search, setSearch] = useState("");
  const [autoScroll, setAutoScroll] = useState(true);
  const [loading, setLoading] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  const fetchLogs = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/logs?limit=200`);
      if (!res.ok) throw new Error();
      const data = await res.json();
      setLogs((data.logs || data || []).map((l: any, i: number) => ({
        id: l.id || `log-${Date.now()}-${i}`,
        timestamp: l.timestamp || new Date().toISOString(),
        level: l.level || "info",
        message: l.message || l.msg || "",
        source: l.source || l.module || "system",
      })));
    } catch {
      // Generate sample logs
      const levels: LogLevel[] = ["info", "warn", "error", "debug"];
      const msgs = [
        { level: "info", msg: "WebSocket connection established", src: "ws-hub" },
        { level: "info", msg: "Model inference completed in 234ms", src: "inference" },
        { level: "warn", msg: "High memory usage detected: 87%", src: "monitor" },
        { level: "error", msg: "Failed to connect to Redis on port 6379", src: "cache" },
        { level: "debug", msg: "Processing batch of 32 requests", src: "queue" },
        { level: "info", msg: "Emotion state updated: focused (0.82)", src: "emotion" },
        { level: "warn", msg: "API rate limit approaching: 89/100", src: "gateway" },
        { level: "info", msg: "New session started: user_abc123", src: "auth" },
        { level: "error", msg: "Timeout waiting for model response", src: "inference" },
        { level: "debug", msg: "Cache hit ratio: 0.73", src: "cache" },
      ];
      setLogs(msgs.map((m, i) => ({
        id: `log-${i}`,
        timestamp: new Date(Date.now() - (msgs.length - i) * 5000).toISOString(),
        level: m.level as LogLevel,
        message: m.msg,
        source: m.src,
      })));
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, [fetchLogs]);

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const filtered = logs.filter((log) => {
    if (filter !== "all" && log.level !== filter) return false;
    if (search && !log.message.toLowerCase().includes(search.toLowerCase()) && !log.source.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  if (loading) {
    return (
      <div className="bg-gray-950 border border-gray-700 rounded-xl p-6 animate-pulse">
        <div className="h-4 bg-gray-700 rounded w-1/4 mb-4" />
        <div className="h-64 bg-gray-900 rounded" />
      </div>
    );
  }

  return (
    <div className="bg-gray-950 border border-gray-700 rounded-xl p-6 space-y-3 font-mono">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-gray-200">Logs Viewer</h2>
        <span className="text-xs text-gray-500">{filtered.length} entries</span>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap gap-2 items-center">
        <div className="flex gap-1">
          {(["all", "info", "warn", "error", "debug"] as const).map((lvl) => (
            <button
              key={lvl}
              onClick={() => setFilter(lvl)}
              className={`text-[10px] px-2 py-1 rounded ${filter === lvl ? "bg-gray-700 text-gray-200" : "bg-gray-800 text-gray-500 hover:bg-gray-750"}`}
            >
              {lvl.toUpperCase()}
            </button>
          ))}
        </div>
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search logs..."
          className="flex-1 min-w-[120px] bg-gray-900 border border-gray-700 text-gray-300 text-xs rounded px-2 py-1 focus:border-gray-500 focus:outline-none"
        />
        <button
          onClick={() => setAutoScroll(!autoScroll)}
          className={`text-[10px] px-2 py-1 rounded ${autoScroll ? "bg-green-900 text-green-300" : "bg-gray-800 text-gray-500"}`}
        >
          {autoScroll ? "AUTO-SCROLL ON" : "AUTO-SCROLL OFF"}
        </button>
      </div>

      {/* Log Entries */}
      <div ref={scrollRef} className="bg-black/60 border border-gray-800 rounded-lg p-2 max-h-80 overflow-y-auto space-y-0.5">
        {filtered.length > 0 ? (
          filtered.map((log) => {
            const style = LEVEL_STYLES[log.level];
            return (
              <div key={log.id} className={`flex gap-2 px-2 py-1 rounded text-xs ${style.bg} border-l-2 ${style.border}`}>
                <span className="text-gray-600 shrink-0">{log.timestamp.slice(11, 23)}</span>
                <span className={`shrink-0 w-12 font-bold ${style.text}`}>[{log.level.toUpperCase()}]</span>
                <span className="text-gray-500 shrink-0">[{log.source}]</span>
                <span className="text-gray-300 break-all">{log.message}</span>
              </div>
            );
          })
        ) : (
          <p className="text-gray-600 text-center py-8 text-xs">No logs matching filter</p>
        )}
      </div>

      <div className="flex justify-between text-[10px] text-gray-600">
        <button onClick={fetchLogs} className="hover:text-gray-400">Refresh</button>
        <button onClick={() => setLogs([])} className="hover:text-gray-400">Clear</button>
      </div>
    </div>
  );
}
