import React, { useState, useEffect, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface Session {
  id: string;
  date: string;
  duration: string;
  durationMin: number;
  actionsCount: number;
  tradesExecuted: number;
  pnl: number;
  status: "completed" | "active" | "interrupted";
}

interface SessionDetail {
  id: string;
  actions: { timestamp: string; type: string; description: string }[];
}

export default function UserSessionHistory() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<"date" | "duration" | "actions">("date");

  const fetchSessions = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/sessions`);
      if (!res.ok) throw new Error();
      const data = await res.json();
      setSessions(data.sessions || data || []);
    } catch {
      setSessions([
        { id: "s1", date: "2024-03-15 14:30", duration: "2h 15m", durationMin: 135, actionsCount: 87, tradesExecuted: 5, pnl: 324.50, status: "completed" },
        { id: "s2", date: "2024-03-14 09:00", duration: "4h 45m", durationMin: 285, actionsCount: 203, tradesExecuted: 12, pnl: -156.20, status: "completed" },
        { id: "s3", date: "2024-03-13 16:20", duration: "1h 30m", durationMin: 90, actionsCount: 45, tradesExecuted: 2, pnl: 89.75, status: "completed" },
        { id: "s4", date: "2024-03-13 08:00", duration: "3h 10m", durationMin: 190, actionsCount: 134, tradesExecuted: 8, pnl: 512.30, status: "completed" },
        { id: "s5", date: "2024-03-12 11:45", duration: "0h 45m", durationMin: 45, actionsCount: 22, tradesExecuted: 0, pnl: 0, status: "interrupted" },
        { id: "s6", date: "2024-03-15 17:00", duration: "0h 35m", durationMin: 35, actionsCount: 15, tradesExecuted: 1, pnl: 45.00, status: "active" },
      ]);
    }
    setLoading(false);
  }, []);

  useEffect(() => { fetchSessions(); }, [fetchSessions]);

  const viewDetail = async (id: string) => {
    if (selectedId === id) { setSelectedId(null); setDetail(null); return; }
    setSelectedId(id);
    setDetail({
      id,
      actions: [
        { timestamp: "14:30:00", type: "navigate", description: "Opened trading dashboard" },
        { timestamp: "14:32:15", type: "analysis", description: "Ran BTC market analysis" },
        { timestamp: "14:35:42", type: "trade", description: "Opened long BTC @ $67,400" },
        { timestamp: "14:45:10", type: "adjustment", description: "Set stop-loss at $66,800" },
        { timestamp: "15:12:30", type: "trade", description: "Closed position @ $67,850 (+$324.50)" },
      ],
    });
  };

  const sorted = [...sessions].sort((a, b) => {
    if (sortBy === "date") return b.date.localeCompare(a.date);
    if (sortBy === "duration") return b.durationMin - a.durationMin;
    return b.actionsCount - a.actionsCount;
  });

  const STATUS_STYLES: Record<string, string> = {
    completed: "bg-green-900 text-green-300",
    active: "bg-blue-900 text-blue-300",
    interrupted: "bg-yellow-900 text-yellow-300",
  };

  if (loading) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 animate-pulse space-y-3">
        <div className="h-4 bg-gray-700 rounded w-1/3" />
        {[1, 2, 3].map((i) => <div key={i} className="h-12 bg-gray-800 rounded" />)}
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-sky-300">Session History</h2>
        <div className="flex gap-1">
          {(["date", "duration", "actions"] as const).map((s) => (
            <button
              key={s}
              onClick={() => setSortBy(s)}
              className={`text-[10px] px-2 py-1 rounded ${sortBy === s ? "bg-sky-800 text-sky-200" : "bg-gray-800 text-gray-500 hover:bg-gray-700"}`}
            >
              {s.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="bg-gray-950 border border-gray-800 rounded-lg overflow-hidden">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-gray-500 border-b border-gray-800">
              <th className="text-left p-2">Date</th>
              <th className="text-left p-2">Duration</th>
              <th className="text-right p-2">Actions</th>
              <th className="text-right p-2">Trades</th>
              <th className="text-right p-2">PnL</th>
              <th className="text-center p-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((session) => (
              <React.Fragment key={session.id}>
                <tr
                  onClick={() => viewDetail(session.id)}
                  className={`border-b border-gray-800/50 cursor-pointer hover:bg-gray-800/30 ${selectedId === session.id ? "bg-gray-800/50" : ""}`}
                >
                  <td className="p-2 text-gray-300">{session.date}</td>
                  <td className="p-2 text-gray-400">{session.duration}</td>
                  <td className="p-2 text-gray-300 text-right">{session.actionsCount}</td>
                  <td className="p-2 text-gray-300 text-right">{session.tradesExecuted}</td>
                  <td className={`p-2 text-right font-mono ${session.pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                    {session.pnl >= 0 ? "+" : ""}{session.pnl.toFixed(2)}
                  </td>
                  <td className="p-2 text-center">
                    <span className={`text-[9px] px-1.5 py-0.5 rounded ${STATUS_STYLES[session.status]}`}>
                      {session.status.toUpperCase()}
                    </span>
                  </td>
                </tr>
                {selectedId === session.id && detail && (
                  <tr>
                    <td colSpan={6} className="p-3 bg-gray-800/30">
                      <div className="space-y-1">
                        {detail.actions.map((a, i) => (
                          <div key={i} className="flex items-center gap-2 text-[10px]">
                            <span className="text-gray-600 font-mono">{a.timestamp}</span>
                            <span className="text-gray-500">[{a.type}]</span>
                            <span className="text-gray-300">{a.description}</span>
                          </div>
                        ))}
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
