import React, { useState, useEffect, useCallback } from "react";

interface Memory {
  id: string;
  content: string;
  category: string;
  timestamp: string;
  importance: number;
}

interface MemoryStats {
  total: number;
  categories: Record<string, number>;
  oldestDate: string;
  newestDate: string;
}

export default function MemoryPanel() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [newMemory, setNewMemory] = useState("");
  const [newCategory, setNewCategory] = useState("general");
  const [saving, setSaving] = useState(false);
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  const fetchMemories = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/memory?search=${encodeURIComponent(search)}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setMemories(data.memories ?? []);
      setStats(data.stats ?? null);
    } catch (e: any) {
      setError(e.message ?? "Failed to load memories");
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => { fetchMemories(); }, [fetchMemories]);

  const storeMemory = async () => {
    if (!newMemory.trim()) return;
    setSaving(true);
    try {
      const res = await fetch("/api/v1/memory", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: newMemory, category: newCategory }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setNewMemory("");
      fetchMemories();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const clearMemories = async () => {
    try {
      const res = await fetch("/api/v1/memory", { method: "DELETE" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setMemories([]);
      setStats(null);
      setShowClearConfirm(false);
    } catch (e: any) {
      setError(e.message);
    }
  };

  const CATEGORIES = ["general", "trading", "analysis", "decision", "insight"];

  const importanceColor = (v: number) =>
    v >= 8 ? "text-red-400" : v >= 5 ? "text-yellow-400" : "text-gray-400";

  return (
    <div className="bg-gray-900 text-white rounded-2xl shadow-lg p-6 space-y-5">
      <h2 className="text-xl font-bold">Memory Browser</h2>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-4 gap-2">
          <div className="bg-gray-800 rounded-lg p-2 text-center">
            <p className="text-xs text-gray-500">Total</p>
            <p className="text-lg font-mono font-bold text-cyan-400">{stats.total}</p>
          </div>
          {Object.entries(stats.categories).slice(0, 3).map(([cat, count]) => (
            <div key={cat} className="bg-gray-800 rounded-lg p-2 text-center">
              <p className="text-xs text-gray-500 capitalize">{cat}</p>
              <p className="text-lg font-mono font-bold text-gray-300">{count}</p>
            </div>
          ))}
        </div>
      )}

      {/* Search */}
      <div className="flex gap-2">
        <input value={search} onChange={(e) => setSearch(e.target.value)}
          placeholder="Search memories..."
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-cyan-500" />
        <button onClick={fetchMemories} className="px-3 py-2 text-sm rounded-lg bg-gray-700 hover:bg-gray-600 transition">
          Search
        </button>
      </div>

      {loading && (
        <div className="flex justify-center py-8">
          <div className="animate-spin h-8 w-8 border-4 border-cyan-400 border-t-transparent rounded-full" />
        </div>
      )}

      {error && (
        <div className="bg-red-900/40 border border-red-500 text-red-300 rounded-lg p-3 text-sm">{error}</div>
      )}

      {/* Memory list */}
      {!loading && (
        <div className="max-h-60 overflow-y-auto space-y-2 pr-1">
          {memories.length === 0 ? (
            <p className="text-sm text-gray-600 text-center py-4">No memories found.</p>
          ) : (
            memories.map((m) => (
              <div key={m.id} className="bg-gray-800 border border-gray-700/50 rounded-lg p-3">
                <div className="flex items-start justify-between mb-1">
                  <span className="text-xs px-1.5 py-0.5 rounded bg-gray-700 text-gray-400 capitalize">{m.category}</span>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-mono ${importanceColor(m.importance)}`}>
                      imp:{m.importance}
                    </span>
                    <span className="text-xs text-gray-600">{new Date(m.timestamp).toLocaleString()}</span>
                  </div>
                </div>
                <p className="text-sm text-gray-300 mt-1">{m.content}</p>
              </div>
            ))
          )}
        </div>
      )}

      {/* Store new memory */}
      <div className="bg-gray-800 rounded-xl p-4 space-y-3">
        <h3 className="text-sm font-semibold text-gray-400">Store New Memory</h3>
        <textarea value={newMemory} onChange={(e) => setNewMemory(e.target.value)}
          placeholder="Enter a new memory or insight..."
          rows={2}
          className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:border-cyan-500" />
        <div className="flex items-center gap-2">
          <select value={newCategory} onChange={(e) => setNewCategory(e.target.value)}
            className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-cyan-500">
            {CATEGORIES.map((c) => (
              <option key={c} value={c} className="capitalize">{c}</option>
            ))}
          </select>
          <button onClick={storeMemory} disabled={saving || !newMemory.trim()}
            className="flex-1 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:bg-gray-700 disabled:text-gray-500 text-sm font-semibold transition">
            {saving ? "Storing..." : "Store Memory"}
          </button>
        </div>
      </div>

      {/* Clear */}
      <div className="flex justify-end">
        {!showClearConfirm ? (
          <button onClick={() => setShowClearConfirm(true)}
            className="text-xs text-gray-600 hover:text-red-400 transition">
            Clear All Memories
          </button>
        ) : (
          <div className="flex items-center gap-2">
            <span className="text-xs text-red-400">Are you sure?</span>
            <button onClick={clearMemories} className="text-xs px-2 py-1 rounded bg-red-700 hover:bg-red-600 text-white">
              Yes, Clear
            </button>
            <button onClick={() => setShowClearConfirm(false)} className="text-xs px-2 py-1 rounded bg-gray-700 hover:bg-gray-600">
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
