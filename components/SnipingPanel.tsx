import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";

interface SnipeConfig {
  maxBuyAmount: string;
  slippage: string;
  autoBuy: boolean;
  antiRugCheck: boolean;
}

interface RecentSnipe {
  id: string;
  symbol: string;
  status: "success" | "failed" | "pending";
  amount: number;
  price: number;
  timestamp: string;
  antiRugScore: number;
}

interface NewToken {
  symbol: string;
  name: string;
  chain: string;
  liquidity: number;
  age: string;
  antiRugScore: number;
}

const SnipingPanel: React.FC = () => {
  const [config, setConfig] = useState<SnipeConfig>({
    maxBuyAmount: "0.1", slippage: "5", autoBuy: false, antiRugCheck: true,
  });
  const [newTokens, setNewTokens] = useState<NewToken[]>([]);
  const [recentSnipes, setRecentSnipes] = useState<RecentSnipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sniping, setSniping] = useState<string | null>(null);
  const [symbol, setSymbol] = useState("");

  const fetchData = useCallback(async () => {
    try {
      const [tokensRes, snipesRes] = await Promise.allSettled([
        axios.get(`${process.env.NEXT_PUBLIC_API_URL || ""}/api/sniping/new-tokens`),
        axios.get(`${process.env.NEXT_PUBLIC_API_URL || ""}/api/sniping/history`),
      ]);
      if (tokensRes.status === "fulfilled") setNewTokens(tokensRes.value.data?.tokens || []);
      if (snipesRes.status === "fulfilled") setRecentSnipes(snipesRes.value.data?.snipes || []);
      setError(null);
    } catch {
      setError("Failed to fetch sniping data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const executeSnipe = async (tokenSymbol: string) => {
    setSniping(tokenSymbol);
    setError(null);
    try {
      const res = await axios.post(`${process.env.NEXT_PUBLIC_API_URL || ""}/api/chat`, {
        message: `Snippea el token ${tokenSymbol}`,
        user: "gorilla_user",
      });
      setRecentSnipes((prev) => [{
        id: `snipe-${Date.now()}`, symbol: tokenSymbol, status: "success",
        amount: parseFloat(config.maxBuyAmount), price: 0, timestamp: new Date().toISOString(),
        antiRugScore: 0,
      }, ...prev]);
    } catch (err: any) {
      setError(err?.response?.data?.error || "Snipe failed");
    } finally {
      setSniping(null);
    }
  };

  const handleManualSnipe = () => {
    if (symbol.trim()) {
      executeSnipe(symbol.trim());
      setSymbol("");
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-400";
    if (score >= 50) return "text-yellow-400";
    return "text-red-400";
  };

  const getStatusStyle = (status: string) => {
    if (status === "success") return "bg-green-800 text-green-300";
    if (status === "failed") return "bg-red-800 text-red-300";
    return "bg-yellow-800 text-yellow-300";
  };

  return (
    <div className="bg-gray-900 text-white rounded-xl border border-gray-700 overflow-hidden">
      <div className="px-4 py-3 bg-gray-800 border-b border-gray-700">
        <h2 className="text-lg font-semibold">Token Sniping</h2>
      </div>

      <div className="p-4 space-y-4">
        {error && <div className="bg-red-900/40 border border-red-700 text-red-300 px-3 py-2 rounded text-xs">{error}</div>}

        {/* Manual Snipe */}
        <div className="flex gap-2">
          <input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            placeholder="Token symbol (e.g. PEPE)"
            className="flex-1 bg-gray-700 text-white text-sm rounded px-3 py-2 border border-gray-600 focus:outline-none focus:ring-1 focus:ring-blue-500"
            onKeyDown={(e) => e.key === "Enter" && handleManualSnipe()} />
          <button onClick={handleManualSnipe} disabled={!symbol.trim() || !!sniping}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-700 px-4 py-2 rounded text-sm font-medium transition">
            Snipe
          </button>
        </div>

        {/* Configuration */}
        <div className="bg-gray-800 rounded-lg p-3 space-y-2">
          <h4 className="text-xs font-semibold text-gray-400 uppercase">Configuration</h4>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-[10px] text-gray-500">Max Buy (ETH/SOL)</label>
              <input type="number" step="0.01" value={config.maxBuyAmount}
                onChange={(e) => setConfig({ ...config, maxBuyAmount: e.target.value })}
                className="w-full bg-gray-700 text-white text-xs rounded px-2 py-1.5 border border-gray-600" />
            </div>
            <div>
              <label className="text-[10px] text-gray-500">Slippage %</label>
              <input type="number" step="0.5" value={config.slippage}
                onChange={(e) => setConfig({ ...config, slippage: e.target.value })}
                className="w-full bg-gray-700 text-white text-xs rounded px-2 py-1.5 border border-gray-600" />
            </div>
          </div>
          <div className="flex gap-4">
            <label className="flex items-center gap-1.5 text-xs text-gray-300 cursor-pointer">
              <input type="checkbox" checked={config.autoBuy}
                onChange={(e) => setConfig({ ...config, autoBuy: e.target.checked })}
                className="rounded border-gray-600 bg-gray-700 text-blue-500" />
              Auto-buy
            </label>
            <label className="flex items-center gap-1.5 text-xs text-gray-300 cursor-pointer">
              <input type="checkbox" checked={config.antiRugCheck}
                onChange={(e) => setConfig({ ...config, antiRugCheck: e.target.checked })}
                className="rounded border-gray-600 bg-gray-700 text-blue-500" />
              Anti-rug check
            </label>
          </div>
        </div>

        {/* New Tokens Monitor */}
        <div>
          <h4 className="text-xs font-semibold text-gray-400 uppercase mb-2">New Tokens Detected</h4>
          {loading ? (
            <div className="text-center text-gray-500 text-xs py-4">Monitoring...</div>
          ) : newTokens.length === 0 ? (
            <div className="text-center text-gray-600 text-xs py-4">No new tokens detected</div>
          ) : (
            <div className="space-y-1.5 max-h-40 overflow-y-auto">
              {newTokens.map((token, i) => (
                <div key={i} className="flex items-center justify-between bg-gray-800 rounded px-3 py-2 text-xs">
                  <div className="flex items-center gap-2 min-w-0">
                    <div>
                      <span className="font-medium">{token.symbol}</span>
                      <span className="text-gray-500 ml-1">{token.name}</span>
                    </div>
                    <span className="text-[10px] text-gray-500">{token.chain}</span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className={`font-mono ${getScoreColor(token.antiRugScore)}`}>
                      {token.antiRugScore}/100
                    </span>
                    <button onClick={() => executeSnipe(token.symbol)} disabled={!!sniping}
                      className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 px-2 py-0.5 rounded text-[10px] transition">
                      {sniping === token.symbol ? "..." : "Snipe"}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Snipes */}
        <div>
          <h4 className="text-xs font-semibold text-gray-400 uppercase mb-2">Recent Snipes</h4>
          {recentSnipes.length === 0 ? (
            <div className="text-center text-gray-600 text-xs py-4">No recent snipes</div>
          ) : (
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {recentSnipes.slice(0, 10).map((snipe) => (
                <div key={snipe.id} className="flex items-center justify-between bg-gray-800 rounded px-3 py-1.5 text-xs">
                  <div className="flex items-center gap-2">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${getStatusStyle(snipe.status)}`}>
                      {snipe.status.toUpperCase()}
                    </span>
                    <span className="font-medium">{snipe.symbol}</span>
                  </div>
                  <span className="text-gray-500 text-[10px]">{new Date(snipe.timestamp).toLocaleTimeString()}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SnipingPanel;
