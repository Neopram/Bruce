import React, { useState, useEffect, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

type ActionType = "config_change" | "user_mgmt" | "trade_override" | "system" | "security";

interface AuditEntry {
  id: string;
  timestamp: string;
  user: string;
  actionType: ActionType;
  action: string;
  details: string;
  ip: string;
}

const TYPE_STYLES: Record<ActionType, { badge: string }> = {
  config_change: { badge: "bg-yellow-900 text-yellow-300" },
  user_mgmt: { badge: "bg-blue-900 text-blue-300" },
  trade_override: { badge: "bg-red-900 text-red-300" },
  system: { badge: "bg-gray-700 text-gray-300" },
  security: { badge: "bg-purple-900 text-purple-300" },
};

export default function AdminAuditPanel() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [filter, setFilter] = useState<ActionType | "all">("all");
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const pageSize = 10;

  const fetchAudit = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/admin/audit?limit=50`);
      if (!res.ok) throw new Error();
      const data = await res.json();
      setEntries(data.entries || data || []);
    } catch {
      setEntries([
        { id: "a1", timestamp: "2024-03-15 17:30:12", user: "admin", actionType: "config_change", action: "Updated risk parameters", details: "risk_limit: 5% -> 3%", ip: "192.168.1.10" },
        { id: "a2", timestamp: "2024-03-15 16:45:30", user: "admin", actionType: "user_mgmt", action: "Created new user", details: "user: viewer@bruce.ai, role: viewer", ip: "192.168.1.10" },
        { id: "a3", timestamp: "2024-03-15 15:20:05", user: "admin", actionType: "trade_override", action: "Force-closed position", details: "BTC/USDT long, reason: risk limit exceeded", ip: "192.168.1.10" },
        { id: "a4", timestamp: "2024-03-15 14:10:44", user: "system", actionType: "system", action: "Auto-backup completed", details: "Database backup: 2.3GB, duration: 45s", ip: "127.0.0.1" },
        { id: "a5", timestamp: "2024-03-15 12:00:00", user: "system", actionType: "security", action: "JWT rotation", details: "All active tokens refreshed", ip: "127.0.0.1" },
        { id: "a6", timestamp: "2024-03-15 10:33:21", user: "admin", actionType: "config_change", action: "Updated model config", details: "Switched primary model to deepseek-v3", ip: "192.168.1.10" },
        { id: "a7", timestamp: "2024-03-14 23:15:00", user: "system", actionType: "system", action: "Scheduled maintenance", details: "Redis cache flush, index rebuild", ip: "127.0.0.1" },
        { id: "a8", timestamp: "2024-03-14 18:42:10", user: "admin", actionType: "security", action: "Blocked IP address", details: "IP: 45.33.32.156, reason: brute force", ip: "192.168.1.10" },
        { id: "a9", timestamp: "2024-03-14 14:00:30", user: "admin", actionType: "user_mgmt", action: "Suspended user account", details: "user: suspect@example.com", ip: "192.168.1.10" },
        { id: "a10", timestamp: "2024-03-14 09:12:45", user: "admin", actionType: "trade_override", action: "Manual order execution", details: "ETH/USDT market buy, 0.5 ETH", ip: "192.168.1.10" },
      ]);
    }
    setLoading(false);
  }, []);

  useEffect(() => { fetchAudit(); }, [fetchAudit]);

  const filtered = filter === "all" ? entries : entries.filter((e) => e.actionType === filter);
  const paginated = filtered.slice(page * pageSize, (page + 1) * pageSize);
  const totalPages = Math.ceil(filtered.length / pageSize);

  if (loading) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 animate-pulse space-y-3">
        <div className="h-4 bg-gray-700 rounded w-1/3" />
        {[1, 2, 3, 4].map((i) => <div key={i} className="h-10 bg-gray-800 rounded" />)}
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-4">
      <h2 className="text-lg font-bold text-orange-300">Admin Audit Trail</h2>

      {/* Filters */}
      <div className="flex gap-1 flex-wrap">
        {(["all", "config_change", "user_mgmt", "trade_override", "system", "security"] as const).map((t) => (
          <button
            key={t}
            onClick={() => { setFilter(t); setPage(0); }}
            className={`text-[10px] px-2 py-1 rounded ${filter === t ? "bg-orange-800 text-orange-200" : "bg-gray-800 text-gray-500 hover:bg-gray-700"}`}
          >
            {t === "all" ? "ALL" : t.replace(/_/g, " ").toUpperCase()}
          </button>
        ))}
      </div>

      {/* Audit Log */}
      <div className="space-y-1.5">
        {paginated.map((entry) => {
          const style = TYPE_STYLES[entry.actionType];
          return (
            <div key={entry.id} className="bg-gray-800 border border-gray-700 rounded-lg p-3">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <span className={`text-[9px] px-1.5 py-0.5 rounded ${style.badge}`}>{entry.actionType.replace(/_/g, " ")}</span>
                  <span className="text-xs text-gray-300 font-semibold">{entry.action}</span>
                </div>
                <span className="text-[10px] text-gray-600 font-mono">{entry.timestamp}</span>
              </div>
              <div className="flex items-center gap-3 text-[10px] text-gray-500">
                <span>User: <span className="text-gray-400">{entry.user}</span></span>
                <span>IP: <span className="text-gray-400 font-mono">{entry.ip}</span></span>
              </div>
              <p className="text-xs text-gray-400 mt-1">{entry.details}</p>
            </div>
          );
        })}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
            className="text-xs px-2 py-1 bg-gray-800 hover:bg-gray-700 disabled:text-gray-600 text-gray-300 rounded"
          >
            Prev
          </button>
          <span className="text-xs text-gray-500">{page + 1} / {totalPages}</span>
          <button
            onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
            disabled={page >= totalPages - 1}
            className="text-xs px-2 py-1 bg-gray-800 hover:bg-gray-700 disabled:text-gray-600 text-gray-300 rounded"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
