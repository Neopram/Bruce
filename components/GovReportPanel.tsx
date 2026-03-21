import React, { useState, useEffect, useCallback } from "react";

interface Decision {
  id: string;
  institution: string;
  date: string;
  type: "rate_change" | "policy" | "statement";
  title: string;
  detail: string;
  impact: "hawkish" | "dovish" | "neutral";
  rateChange?: number;
}

const IMPACT_STYLES: Record<string, { color: string; bg: string; label: string }> = {
  hawkish: { color: "text-red-400", bg: "bg-red-900/30", label: "Hawkish" },
  dovish:  { color: "text-green-400", bg: "bg-green-900/30", label: "Dovish" },
  neutral: { color: "text-gray-400", bg: "bg-gray-800", label: "Neutral" },
};

const TYPE_ICON: Record<string, string> = {
  rate_change: "\u2191\u2193",
  policy: "\uD83D\uDCC4",
  statement: "\uD83D\uDDE3",
};

export default function GovReportPanel() {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "rate_change" | "policy" | "statement">("all");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/v1/gov/decisions");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setDecisions(data.decisions ?? []);
    } catch (e: any) {
      setError(e.message ?? "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const filtered = filter === "all" ? decisions : decisions.filter((d) => d.type === filter);

  const rateChanges = decisions.filter((d) => d.rateChange !== undefined);
  const latestRate = rateChanges.length > 0 ? rateChanges[0] : null;

  return (
    <div className="bg-gray-900 text-white rounded-2xl shadow-lg p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Government Reports</h2>
        <button onClick={fetchData} className="px-3 py-1 text-sm rounded bg-gray-700 hover:bg-gray-600 transition">
          Refresh
        </button>
      </div>

      {loading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin h-8 w-8 border-4 border-cyan-400 border-t-transparent rounded-full" />
        </div>
      )}

      {error && (
        <div className="bg-red-900/40 border border-red-500 text-red-300 rounded-lg p-4">
          <p className="text-sm">{error}</p>
          <button onClick={fetchData} className="mt-2 text-sm underline hover:text-red-200">Retry</button>
        </div>
      )}

      {!loading && !error && (
        <>
          {/* Rate summary */}
          {latestRate && (
            <div className="bg-gray-800 rounded-xl p-4 flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500">Latest Rate Decision</p>
                <p className="text-sm font-medium">{latestRate.institution}</p>
              </div>
              <div className="text-right">
                <span className={`text-2xl font-mono font-bold ${latestRate.rateChange! > 0 ? "text-red-400" : latestRate.rateChange! < 0 ? "text-green-400" : "text-gray-400"}`}>
                  {latestRate.rateChange! > 0 ? "+" : ""}{latestRate.rateChange}bps
                </span>
                <p className="text-xs text-gray-500">{new Date(latestRate.date).toLocaleDateString()}</p>
              </div>
            </div>
          )}

          {/* Filters */}
          <div className="flex gap-2">
            {[
              { key: "all" as const, label: "All" },
              { key: "rate_change" as const, label: "Rate Changes" },
              { key: "policy" as const, label: "Policy" },
              { key: "statement" as const, label: "Statements" },
            ].map((f) => (
              <button key={f.key} onClick={() => setFilter(f.key)}
                className={`px-3 py-1.5 rounded-lg text-sm transition ${
                  filter === f.key ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                }`}>
                {f.label}
              </button>
            ))}
          </div>

          {/* Timeline */}
          <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
            {filtered.length === 0 ? (
              <p className="text-sm text-gray-600 text-center py-4">No decisions found.</p>
            ) : (
              filtered.map((d) => {
                const impact = IMPACT_STYLES[d.impact] ?? IMPACT_STYLES.neutral;
                return (
                  <div key={d.id} className={`${impact.bg} border border-gray-700/50 rounded-xl p-4`}>
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-sm">{TYPE_ICON[d.type] ?? ""}</span>
                        <div>
                          <p className="text-sm font-semibold">{d.title}</p>
                          <p className="text-xs text-gray-500">{d.institution} - {new Date(d.date).toLocaleDateString()}</p>
                        </div>
                      </div>
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded ${impact.color} ${impact.bg}`}>
                        {impact.label}
                      </span>
                    </div>
                    <p className="text-sm text-gray-400">{d.detail}</p>
                    {d.rateChange !== undefined && (
                      <p className={`text-sm font-mono mt-1 ${d.rateChange > 0 ? "text-red-400" : d.rateChange < 0 ? "text-green-400" : "text-gray-400"}`}>
                        Rate change: {d.rateChange > 0 ? "+" : ""}{d.rateChange}bps
                      </p>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </>
      )}
    </div>
  );
}
