import React, { useEffect, useState, useCallback } from "react";
import axios from "axios";

interface ArbitrageOpportunity {
  id: string;
  pair: string;
  exchangeA: string;
  exchangeB: string;
  priceA: number;
  priceB: number;
  spreadPct: number;
  estimatedProfit: number;
  volume: number;
}

const ArbitragePanel: React.FC = () => {
  const [opportunities, setOpportunities] = useState<ArbitrageOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [executing, setExecuting] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchOpportunities = useCallback(async () => {
    try {
      const res = await axios.get(
        `${process.env.NEXT_PUBLIC_API_URL || ""}/api/arbitrage/opportunities`
      );
      const raw = res.data?.opportunities || res.data || [];
      const mapped: ArbitrageOpportunity[] = raw.map((arb: any, idx: number) => {
        if (Array.isArray(arb)) {
          return {
            id: `arb-${idx}`,
            pair: arb[0] || "N/A",
            exchangeA: arb[1] || "Exchange A",
            exchangeB: arb[2] || "Exchange B",
            priceA: 0,
            priceB: 0,
            spreadPct: 0,
            estimatedProfit: parseFloat(arb[3]) || 0,
            volume: 0,
          };
        }
        return {
          id: arb.id || `arb-${idx}`,
          pair: arb.pair || "N/A",
          exchangeA: arb.exchangeA || arb.exchange_a || "Exchange A",
          exchangeB: arb.exchangeB || arb.exchange_b || "Exchange B",
          priceA: arb.priceA || arb.price_a || 0,
          priceB: arb.priceB || arb.price_b || 0,
          spreadPct: arb.spreadPct || arb.spread_pct || 0,
          estimatedProfit: arb.estimatedProfit || arb.estimated_profit || 0,
          volume: arb.volume || 0,
        };
      });
      setOpportunities(mapped);
      setLastUpdated(new Date());
      setError(null);
    } catch (err: any) {
      setError(err?.response?.data?.error || "Failed to fetch arbitrage data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOpportunities();
    if (!autoRefresh) return;
    const interval = setInterval(fetchOpportunities, 5000);
    return () => clearInterval(interval);
  }, [fetchOpportunities, autoRefresh]);

  const executeArbitrage = async (opp: ArbitrageOpportunity) => {
    setExecuting(opp.id);
    try {
      await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL || ""}/api/arbitrage/execute`,
        { pair: opp.pair, exchangeA: opp.exchangeA, exchangeB: opp.exchangeB }
      );
      setOpportunities((prev) => prev.filter((o) => o.id !== opp.id));
    } catch (err: any) {
      setError(err?.response?.data?.error || "Execution failed");
    } finally {
      setExecuting(null);
    }
  };

  return (
    <div className="bg-gray-900 text-white rounded-xl border border-gray-700 overflow-hidden">
      <div className="px-4 py-3 bg-gray-800 border-b border-gray-700 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Arbitrage Opportunities</h2>
          {lastUpdated && (
            <p className="text-[10px] text-gray-500">Updated: {lastUpdated.toLocaleTimeString()}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setAutoRefresh(!autoRefresh)}
            className={`text-xs px-2 py-1 rounded transition ${autoRefresh ? "bg-green-700 text-green-200" : "bg-gray-700 text-gray-400"}`}>
            {autoRefresh ? "Auto: ON" : "Auto: OFF"}
          </button>
          <button onClick={fetchOpportunities} className="text-xs text-gray-400 hover:text-white transition">Refresh</button>
        </div>
      </div>

      <div className="p-4">
        {error && <div className="bg-red-900/40 border border-red-700 text-red-300 px-3 py-2 rounded text-xs mb-3">{error}</div>}

        {loading ? (
          <div className="text-center text-gray-500 text-sm py-8">Scanning for opportunities...</div>
        ) : opportunities.length === 0 ? (
          <div className="text-center text-gray-500 text-sm py-8">No active arbitrage opportunities</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-gray-400 border-b border-gray-700">
                  <th className="py-2 px-2 text-left">Pair</th>
                  <th className="py-2 px-2 text-left">Exchange A</th>
                  <th className="py-2 px-2 text-left">Exchange B</th>
                  <th className="py-2 px-2 text-right">Spread %</th>
                  <th className="py-2 px-2 text-right">Est. Profit</th>
                  <th className="py-2 px-2 text-center">Action</th>
                </tr>
              </thead>
              <tbody>
                {opportunities.map((opp) => (
                  <tr key={opp.id} className="border-b border-gray-800 hover:bg-gray-800/50 transition">
                    <td className="py-2 px-2 font-medium">{opp.pair}</td>
                    <td className="py-2 px-2 text-gray-400">{opp.exchangeA}</td>
                    <td className="py-2 px-2 text-gray-400">{opp.exchangeB}</td>
                    <td className="py-2 px-2 text-right font-mono">
                      <span className={opp.spreadPct >= 1 ? "text-green-400" : "text-yellow-400"}>
                        {opp.spreadPct.toFixed(2)}%
                      </span>
                    </td>
                    <td className="py-2 px-2 text-right font-mono text-green-400">${opp.estimatedProfit.toFixed(2)}</td>
                    <td className="py-2 px-2 text-center">
                      <button
                        onClick={() => executeArbitrage(opp)}
                        disabled={executing === opp.id}
                        className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 px-2 py-1 rounded text-[10px] font-medium transition"
                      >
                        {executing === opp.id ? "..." : "Execute"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default ArbitragePanel;
