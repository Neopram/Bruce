import React, { useState } from "react";

interface TokenResult {
  address: string;
  txHash: string;
  chain: string;
  name: string;
  symbol: string;
  supply: string;
}

const CHAINS = [
  { id: "ethereum", label: "Ethereum", color: "#627eea" },
  { id: "bsc", label: "BSC", color: "#f3ba2f" },
  { id: "polygon", label: "Polygon", color: "#8247e5" },
  { id: "solana", label: "Solana", color: "#14f195" },
  { id: "avalanche", label: "Avalanche", color: "#e84142" },
];

export default function TokenCreator() {
  const [name, setName] = useState("");
  const [symbol, setSymbol] = useState("");
  const [supply, setSupply] = useState("");
  const [chain, setChain] = useState("ethereum");
  const [decimals, setDecimals] = useState("18");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TokenResult | null>(null);

  const isValid = name.trim() && symbol.trim() && supply.trim() && Number(supply) > 0;

  const createToken = async () => {
    if (!isValid) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("/api/v1/tokens/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, symbol: symbol.toUpperCase(), supply, chain, decimals: Number(decimals) }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setResult(await res.json());
    } catch (e: any) {
      setError(e.message ?? "Token creation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gray-900 text-white rounded-2xl shadow-lg p-6 space-y-5">
      <h2 className="text-xl font-bold">Token Creator</h2>
      <p className="text-sm text-gray-400">Deploy a new ERC-20 / SPL token</p>

      <div className="space-y-3">
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Token Name</label>
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Bruce Token"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-cyan-500" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Symbol</label>
            <input value={symbol} onChange={(e) => setSymbol(e.target.value)} placeholder="e.g. BWT" maxLength={8}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm uppercase focus:outline-none focus:border-cyan-500" />
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Decimals</label>
            <input type="number" value={decimals} onChange={(e) => setDecimals(e.target.value)} min="0" max="18"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-cyan-500" />
          </div>
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Total Supply</label>
          <input type="number" value={supply} onChange={(e) => setSupply(e.target.value)} placeholder="e.g. 1000000"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-cyan-500" />
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Chain</label>
          <div className="grid grid-cols-5 gap-2">
            {CHAINS.map((c) => (
              <button key={c.id} onClick={() => setChain(c.id)}
                className={`py-2 rounded-lg text-xs font-medium border transition ${
                  chain === c.id ? "border-cyan-500 bg-gray-800" : "border-gray-700 bg-gray-800/50 text-gray-500 hover:border-gray-600"
                }`}>
                <span className="w-2 h-2 rounded-full inline-block mr-1" style={{ backgroundColor: c.color }} />
                {c.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <button onClick={createToken} disabled={loading || !isValid}
        className="w-full py-2.5 rounded-lg bg-green-600 hover:bg-green-500 disabled:bg-gray-700 disabled:text-gray-500 font-semibold transition">
        {loading ? "Creating..." : "Create Token"}
      </button>

      {error && (
        <div className="bg-red-900/40 border border-red-500 text-red-300 rounded-lg p-3 text-sm">{error}</div>
      )}

      {result && (
        <div className="bg-gray-800 rounded-xl p-4 space-y-3">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-green-400" />
            <span className="text-sm font-semibold text-green-400">Token Created Successfully</span>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-gray-500">Name</span><span>{result.name}</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Symbol</span><span className="font-mono">{result.symbol}</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Chain</span><span className="capitalize">{result.chain}</span></div>
            <div>
              <span className="text-gray-500 block mb-1">Contract Address</span>
              <div className="bg-gray-900 rounded-lg p-2 font-mono text-xs text-cyan-400 break-all">{result.address}</div>
            </div>
            <div>
              <span className="text-gray-500 block mb-1">Transaction Hash</span>
              <div className="bg-gray-900 rounded-lg p-2 font-mono text-xs text-gray-400 break-all">{result.txHash}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
