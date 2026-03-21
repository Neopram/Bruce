import React, { useState, useEffect, useMemo } from "react";
import axios from "axios";

interface Transaction {
  id: string;
  date: string;
  pair: string;
  side: "buy" | "sell";
  amount: number;
  price: number;
  pnl: number;
}

type SortField = "date" | "pair" | "side" | "amount" | "price" | "pnl";
type SortDir = "asc" | "desc";

const CryptoTransactionViewer: React.FC = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterPair, setFilterPair] = useState("");
  const [filterSide, setFilterSide] = useState<"" | "buy" | "sell">("");
  const [filterDateFrom, setFilterDateFrom] = useState("");
  const [filterDateTo, setFilterDateTo] = useState("");
  const [sortField, setSortField] = useState<SortField>("date");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  useEffect(() => {
    const fetchTx = async () => {
      try {
        const res = await axios.get("/api/trading/transactions");
        setTransactions(res.data?.transactions || []);
        setError(null);
      } catch (err: any) {
        setError(err?.response?.data?.error || "Failed to load transactions");
      } finally {
        setLoading(false);
      }
    };
    fetchTx();
  }, []);

  const pairs = useMemo(() => Array.from(new Set(transactions.map((t) => t.pair))), [transactions]);

  const filtered = useMemo(() => {
    let result = [...transactions];
    if (filterPair) result = result.filter((t) => t.pair === filterPair);
    if (filterSide) result = result.filter((t) => t.side === filterSide);
    if (filterDateFrom) result = result.filter((t) => t.date >= filterDateFrom);
    if (filterDateTo) result = result.filter((t) => t.date <= filterDateTo);

    result.sort((a, b) => {
      let valA: any = a[sortField];
      let valB: any = b[sortField];
      if (sortField === "date") { valA = new Date(valA).getTime(); valB = new Date(valB).getTime(); }
      if (valA < valB) return sortDir === "asc" ? -1 : 1;
      if (valA > valB) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
    return result;
  }, [transactions, filterPair, filterSide, filterDateFrom, filterDateTo, sortField, sortDir]);

  const totalPnl = useMemo(() => filtered.reduce((sum, t) => sum + t.pnl, 0), [filtered]);

  const handleSort = (field: SortField) => {
    if (sortField === field) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setSortField(field); setSortDir("desc"); }
  };

  const sortIndicator = (field: SortField) => {
    if (sortField !== field) return "";
    return sortDir === "asc" ? " ^" : " v";
  };

  return (
    <div className="bg-gray-900 text-white rounded-xl border border-gray-700 overflow-hidden">
      <div className="px-4 py-3 bg-gray-800 border-b border-gray-700">
        <h2 className="text-lg font-semibold">Transaction History</h2>
      </div>

      <div className="p-4 space-y-3">
        {error && <div className="bg-red-900/40 border border-red-700 text-red-300 px-3 py-2 rounded text-xs">{error}</div>}

        {/* Filters */}
        <div className="flex flex-wrap gap-2">
          <select value={filterPair} onChange={(e) => setFilterPair(e.target.value)}
            className="bg-gray-800 text-white text-xs rounded px-2 py-1.5 border border-gray-600">
            <option value="">All Pairs</option>
            {pairs.map((p) => <option key={p}>{p}</option>)}
          </select>
          <select value={filterSide} onChange={(e) => setFilterSide(e.target.value as any)}
            className="bg-gray-800 text-white text-xs rounded px-2 py-1.5 border border-gray-600">
            <option value="">All Sides</option>
            <option value="buy">Buy</option>
            <option value="sell">Sell</option>
          </select>
          <input type="date" value={filterDateFrom} onChange={(e) => setFilterDateFrom(e.target.value)}
            className="bg-gray-800 text-white text-xs rounded px-2 py-1.5 border border-gray-600" placeholder="From" />
          <input type="date" value={filterDateTo} onChange={(e) => setFilterDateTo(e.target.value)}
            className="bg-gray-800 text-white text-xs rounded px-2 py-1.5 border border-gray-600" placeholder="To" />
        </div>

        {/* Table */}
        {loading ? (
          <div className="text-center text-gray-500 text-sm py-8">Loading transactions...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-gray-400 border-b border-gray-700">
                  {(["date", "pair", "side", "amount", "price", "pnl"] as SortField[]).map((f) => (
                    <th key={f} onClick={() => handleSort(f)}
                      className="py-2 px-2 text-left cursor-pointer hover:text-white transition whitespace-nowrap">
                      {f.toUpperCase()}{sortIndicator(f)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr><td colSpan={6} className="text-center text-gray-500 py-6">No transactions found</td></tr>
                ) : filtered.map((tx) => (
                  <tr key={tx.id} className="border-b border-gray-800 hover:bg-gray-800/50 transition">
                    <td className="py-2 px-2 text-gray-400">{new Date(tx.date).toLocaleDateString()}</td>
                    <td className="py-2 px-2 font-medium">{tx.pair}</td>
                    <td className="py-2 px-2">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${tx.side === "buy" ? "bg-green-800 text-green-300" : "bg-red-800 text-red-300"}`}>
                        {tx.side.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-2 px-2 font-mono">{tx.amount.toFixed(4)}</td>
                    <td className="py-2 px-2 font-mono">${tx.price.toLocaleString()}</td>
                    <td className={`py-2 px-2 font-mono font-medium ${tx.pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                      {tx.pnl >= 0 ? "+" : ""}${tx.pnl.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Summary */}
        <div className="flex justify-between items-center pt-2 border-t border-gray-700 text-sm">
          <span className="text-gray-400">{filtered.length} transaction{filtered.length !== 1 ? "s" : ""}</span>
          <span className={`font-mono font-semibold ${totalPnl >= 0 ? "text-green-400" : "text-red-400"}`}>
            Total P&L: {totalPnl >= 0 ? "+" : ""}${totalPnl.toFixed(2)}
          </span>
        </div>
      </div>
    </div>
  );
};

export default CryptoTransactionViewer;
