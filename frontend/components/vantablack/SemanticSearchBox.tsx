import React, { useState, useCallback, useRef } from "react";
import { Card, CardContent } from "@/components/ui/card";
import Badge from "@/components/ui/badge";

interface SearchResult {
  id: string;
  content: string;
  score: number;
  source: string;
  type: string;
  highlights?: string[];
}

interface SearchHistoryEntry {
  query: string;
  resultCount: number;
  timestamp: string;
}

export default function SemanticSearchBox() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<SearchHistoryEntry[]>([]);
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const search = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setSelectedResult(null);
    try {
      const res = await fetch(`/vantablack/search?query=${encodeURIComponent(query)}`);
      if (!res.ok) throw new Error(`Search failed (${res.status})`);
      const data = await res.json();

      const parsed: SearchResult[] = Array.isArray(data.results)
        ? data.results.map((r: any, i: number) => ({
            id: r.id || `res-${i}`,
            content: typeof r === "string" ? r : r.content || r.text || JSON.stringify(r),
            score: r.score || 1 - i * 0.1,
            source: r.source || "memory",
            type: r.type || "semantic",
            highlights: r.highlights,
          }))
        : typeof data.results === "string"
        ? [{ id: "res-0", content: data.results, score: 1, source: "memory", type: "semantic" }]
        : [];

      setResults(parsed);
      setHistory((prev) =>
        [{ query, resultCount: parsed.length, timestamp: new Date().toISOString() }, ...prev].slice(0, 10)
      );
    } catch (err: any) {
      setError(err.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [query]);

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return "text-emerald-400";
    if (score >= 0.5) return "text-amber-400";
    return "text-zinc-400";
  };

  return (
    <Card className="bg-gradient-to-br from-zinc-900 to-indigo-950/20 border-indigo-800/30">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-white">Cognitive Semantic Search</h2>
          <Badge variant="info" size="sm">{results.length} results</Badge>
        </div>

        {/* Search Input */}
        <div className="flex gap-2 mb-4">
          <div className="relative flex-1">
            <input
              ref={inputRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search memory, episodes, knowledge..."
              className="w-full pl-9 pr-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-white placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              onKeyDown={(e) => e.key === "Enter" && search()}
            />
            <svg className="absolute left-3 top-3 w-4 h-4 text-zinc-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <button
            onClick={search}
            disabled={loading || !query.trim()}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm text-white transition-colors disabled:opacity-50"
          >
            {loading ? "Searching..." : "Search"}
          </button>
        </div>

        {/* Quick History */}
        {history.length > 0 && (
          <div className="flex gap-2 flex-wrap mb-4">
            {history.slice(0, 5).map((h, i) => (
              <button
                key={i}
                onClick={() => { setQuery(h.query); inputRef.current?.focus(); }}
                className="px-2 py-1 text-xs bg-zinc-800/50 hover:bg-indigo-800/30 border border-zinc-700/50 rounded text-zinc-400 hover:text-white transition-colors"
              >
                {h.query} ({h.resultCount})
              </button>
            ))}
          </div>
        )}

        {error && (
          <div className="mb-4 p-2 rounded-lg bg-red-900/30 border border-red-800/50 text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Results */}
        <div className="space-y-2 max-h-[360px] overflow-y-auto">
          {results.length === 0 && !loading ? (
            <p className="text-center text-zinc-500 py-6 text-sm">
              Enter a query to search across cognitive memory and knowledge base.
            </p>
          ) : (
            results.map((r) => (
              <button
                key={r.id}
                onClick={() => setSelectedResult(selectedResult?.id === r.id ? null : r)}
                className="w-full text-left p-3 rounded-lg bg-zinc-800/50 hover:bg-indigo-900/20 border border-zinc-700/50 hover:border-indigo-700/50 transition-all"
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm text-zinc-200 line-clamp-2 flex-1">{r.content}</p>
                  <span className={`text-xs font-mono ${getScoreColor(r.score)}`}>
                    {(r.score * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-1.5">
                  <Badge variant="neutral" size="sm">{r.source}</Badge>
                  <Badge variant="info" size="sm">{r.type}</Badge>
                </div>
                {selectedResult?.id === r.id && r.highlights && (
                  <div className="mt-2 p-2 bg-indigo-900/20 rounded text-xs text-indigo-300">
                    {r.highlights.map((h, i) => (
                      <p key={i} className="mb-1">{h}</p>
                    ))}
                  </div>
                )}
              </button>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
