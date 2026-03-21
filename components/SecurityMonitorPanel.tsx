import React, { useState, useEffect, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface AuthAttempt {
  id: string;
  timestamp: string;
  user: string;
  success: boolean;
  ip: string;
  method: string;
}

interface SecurityData {
  authAttempts: AuthAttempt[];
  rateLimiting: { current: number; max: number; windowSec: number };
  activeSessions: number;
  jwtStatus: "valid" | "expired" | "revoked";
  jwtExpiresIn: number;
  blockedIps: number;
  failedAttempts24h: number;
}

export default function SecurityMonitorPanel() {
  const [data, setData] = useState<SecurityData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSecurity = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/security/status`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const d = await res.json();
      setData(d);
      setError(null);
    } catch {
      setData({
        authAttempts: [
          { id: "1", timestamp: new Date(Date.now() - 120000).toISOString(), user: "admin", success: true, ip: "192.168.1.10", method: "JWT" },
          { id: "2", timestamp: new Date(Date.now() - 90000).toISOString(), user: "api_bot", success: true, ip: "10.0.0.5", method: "API Key" },
          { id: "3", timestamp: new Date(Date.now() - 60000).toISOString(), user: "unknown", success: false, ip: "45.33.32.156", method: "JWT" },
          { id: "4", timestamp: new Date(Date.now() - 30000).toISOString(), user: "admin", success: true, ip: "192.168.1.10", method: "JWT" },
          { id: "5", timestamp: new Date(Date.now() - 10000).toISOString(), user: "unknown", success: false, ip: "203.0.113.42", method: "Basic" },
        ],
        rateLimiting: { current: 67, max: 100, windowSec: 60 },
        activeSessions: 3,
        jwtStatus: "valid",
        jwtExpiresIn: 3540,
        blockedIps: 12,
        failedAttempts24h: 47,
      });
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchSecurity();
    const interval = setInterval(fetchSecurity, 10000);
    return () => clearInterval(interval);
  }, [fetchSecurity]);

  if (loading) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 animate-pulse space-y-3">
        <div className="h-4 bg-gray-700 rounded w-1/3" />
        <div className="grid grid-cols-2 gap-2">{[1, 2, 3, 4].map((i) => <div key={i} className="h-16 bg-gray-800 rounded" />)}</div>
      </div>
    );
  }

  const ratePct = data ? (data.rateLimiting.current / data.rateLimiting.max) * 100 : 0;
  const jwtColor = data?.jwtStatus === "valid" ? "text-green-400" : data?.jwtStatus === "expired" ? "text-yellow-400" : "text-red-400";

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-5">
      <h2 className="text-lg font-bold text-red-300">Security Monitor</h2>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
          <span className="text-xs text-gray-400">Active Sessions</span>
          <p className="text-xl font-bold text-blue-300">{data?.activeSessions}</p>
        </div>
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
          <span className="text-xs text-gray-400">JWT Status</span>
          <p className={`text-sm font-bold mt-1 ${jwtColor}`}>{data?.jwtStatus?.toUpperCase()}</p>
          <span className="text-[10px] text-gray-500">{Math.floor((data?.jwtExpiresIn ?? 0) / 60)}m left</span>
        </div>
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
          <span className="text-xs text-gray-400">Blocked IPs</span>
          <p className="text-xl font-bold text-orange-300">{data?.blockedIps}</p>
        </div>
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
          <span className="text-xs text-gray-400">Failed (24h)</span>
          <p className="text-xl font-bold text-red-400">{data?.failedAttempts24h}</p>
        </div>
      </div>

      {/* Rate Limiting */}
      <div>
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Rate Limit ({data?.rateLimiting.windowSec}s window)</span>
          <span>{data?.rateLimiting.current}/{data?.rateLimiting.max}</span>
        </div>
        <div className="w-full h-2.5 bg-gray-700 rounded overflow-hidden">
          <div className={`h-full rounded transition-all ${ratePct > 85 ? "bg-red-500" : ratePct > 60 ? "bg-yellow-500" : "bg-green-500"}`} style={{ width: `${ratePct}%` }} />
        </div>
      </div>

      {/* Auth Attempts */}
      <div>
        <h3 className="text-sm font-semibold text-gray-400 mb-2">Recent Auth Attempts</h3>
        <div className="bg-gray-950 border border-gray-800 rounded-lg overflow-hidden">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-gray-500 border-b border-gray-800">
                <th className="text-left p-2">Time</th>
                <th className="text-left p-2">User</th>
                <th className="text-left p-2">Method</th>
                <th className="text-left p-2">IP</th>
                <th className="text-left p-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {data?.authAttempts.map((attempt) => (
                <tr key={attempt.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                  <td className="p-2 text-gray-500 font-mono">{attempt.timestamp.slice(11, 19)}</td>
                  <td className="p-2 text-gray-300">{attempt.user}</td>
                  <td className="p-2 text-gray-400">{attempt.method}</td>
                  <td className="p-2 text-gray-500 font-mono">{attempt.ip}</td>
                  <td className="p-2">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${attempt.success ? "bg-green-900 text-green-300" : "bg-red-900 text-red-300"}`}>
                      {attempt.success ? "OK" : "FAIL"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {error && <p className="text-red-400 text-xs">{error}</p>}
    </div>
  );
}
