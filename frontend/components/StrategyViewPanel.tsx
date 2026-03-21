import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";

interface Strategy {
  id: string;
  name: string;
  enabled: boolean;
  signal: "BUY" | "SELL" | "HOLD";
  returnPct: number;
  sharpeRatio: number;
  winRate: number;
  trades: number;
  lastUpdated: string;
}

const SIGNAL_STYLES: Record<string, string> = {
  BUY: "bg-green-600 text-white",
  SELL: "bg-red-600 text-white",
  HOLD: "bg-gray-600 text-gray-300",
};

const StrategyViewPanel: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStrategies = useCallback(async () => {
    try {
      const res = await axios.get("/api/trading/strategies");
      setStrategies(res.data?.strategies || []);
      setError(null);
    } catch (err: any) {
      setError(err?.response?.data?.error || "Failed to load strategies");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStrategies();
    const interval = setInterval(fetchStrategies, 15000);
    return () => clearInterval(interval);
  }, [fetchStrategies]);

  const toggleStrategy = async (id: string, enabled: boolean) => {
    try {
      await axios.patch(`/api/trading/strategies/${id}`, { enabled: !enabled });
      setStrategies((prev) => prev.map((s) => (s.id === id ? { ...s, enabled: !s.enabled } : s)));
    } catch { /* silent */ }
  };

  return (
    <div className="bg-gray-900 text-white rounded-xl border border-gray-700 overflow-hidden">
      <div className="px-4 py-3 bg-gray-800 border-b border-gray-700 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Strategies</h2>
        <button onClick={fetchStrategies} className="text-xs text-gray-400 hover:text-white transition">Refresh</button>
      </div>

      <div className="p-4 space-y-3">
        {error && <div className="bg-red-900/40 border border-red-700 text-red-300 px-3 py-2 rounded text-xs">{error}</div>}

        {loading ? (
          <div className="text-center text-gray-500 text-sm py-8">Loading strategies...</div>
        ) : strategies.length === 0 ? (
          <div className="text-center text-gray-500 text-sm py-8">No strategies available</div>
        ) : (
          <div className="space-y-2">
            {strategies.map((strat) => (
              <div key={strat.id} className="bg-gray-800 rounded-lg p-3 border border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-semibold">{strat.name}</h3>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${SIGNAL_STYLES[strat.signal]}`}>
                      {strat.signal}
                    </span>
                  </div>
                  <button onClick={() => toggleStrategy(strat.id, strat.enabled)}
                    className={`w-9 h-5 rounded-full transition relative ${strat.enabled ? "bg-green-600" : "bg-gray-600"}`}>
                    <span className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-all ${strat.enabled ? "left-4.5" : "left-0.5"}`} />
                  </button>
                </div>

                <div className="grid grid-cols-4 gap-2 text-center">
                  <div>
                    <p className="text-[10px] text-gray-500">Return</p>
                    <p className={`text-sm font-mono font-medium ${strat.returnPct >= 0 ? "text-green-400" : "text-red-400"}`}>
                      {strat.returnPct >= 0 ? "+" : ""}{strat.returnPct.toFixed(2)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-[10px] text-gray-500">Sharpe</p>
                    <p className={`text-sm font-mono font-medium ${strat.sharpeRatio >= 1 ? "text-green-400" : strat.sharpeRatio >= 0 ? "text-yellow-400" : "text-red-400"}`}>
                      {strat.sharpeRatio.toFixed(2)}
                    </p>
                  </div>
                  <div>
                    <p className="text-[10px] text-gray-500">Win Rate</p>
                    <p className="text-sm font-mono font-medium text-blue-400">{strat.winRate.toFixed(1)}%</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-gray-500">Trades</p>
                    <p className="text-sm font-mono font-medium text-gray-300">{strat.trades}</p>
                  </div>
                </div>

                <p className="text-[10px] text-gray-600 mt-2">
                  Updated: {new Date(strat.lastUpdated).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default StrategyViewPanel;
