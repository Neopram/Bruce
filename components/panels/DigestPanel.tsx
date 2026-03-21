import React, { useEffect, useState, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import Badge from "@/components/ui/badge";
import axios from "axios";

interface DigestItem {
  id: string;
  category: string;
  title: string;
  summary: string;
  source: string;
  sentiment: "positive" | "negative" | "neutral";
  relevance: number;
  timestamp: string;
}

interface DigestData {
  items: DigestItem[];
  generatedAt: string;
  marketSummary?: string;
}

const DigestPanel = () => {
  const [digest, setDigest] = useState<DigestData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("all");
  const [rawView, setRawView] = useState(false);

  const fetchDigest = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get("/api/cognitive/digest");
      const data = res.data;
      if (data && typeof data === "object") {
        const items: DigestItem[] = Array.isArray(data.items)
          ? data.items
          : Array.isArray(data)
          ? data.map((d: any, i: number) => ({
              id: `d-${i}`,
              category: d.category || "general",
              title: d.title || `Digest Item ${i + 1}`,
              summary: d.summary || d.content || JSON.stringify(d),
              source: d.source || "system",
              sentiment: d.sentiment || "neutral",
              relevance: d.relevance || 0.5,
              timestamp: d.timestamp || new Date().toISOString(),
            }))
          : [];
        setDigest({
          items,
          generatedAt: data.generatedAt || new Date().toISOString(),
          marketSummary: data.marketSummary,
        });
      } else {
        setDigest({ items: [], generatedAt: new Date().toISOString() });
      }
    } catch (err: any) {
      setError(err.message || "Failed to load digest");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDigest();
  }, [fetchDigest]);

  const sentimentVariant = (s: string) => {
    const map: Record<string, "success" | "error" | "neutral"> = {
      positive: "success", negative: "error", neutral: "neutral",
    };
    return map[s] || "neutral";
  };

  const categories = digest
    ? ["all", ...Array.from(new Set(digest.items.map(i => i.category)))]
    : ["all"];

  const filteredItems = digest?.items.filter(
    i => filter === "all" || i.category === filter
  ) || [];

  return (
    <Card className="bg-zinc-900 border-zinc-800">
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Cognitive Digest</h2>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setRawView(!rawView)}
              className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
            >
              {rawView ? "Formatted" : "Raw JSON"}
            </button>
            <button
              onClick={fetchDigest}
              disabled={loading}
              className="px-3 py-1 text-xs bg-zinc-700 hover:bg-zinc-600 rounded-lg text-zinc-300 transition-colors disabled:opacity-50"
            >
              {loading ? "Loading..." : "Refresh"}
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-3 p-2 rounded-lg bg-red-900/30 border border-red-800/50 text-red-400 text-sm">
            {error}
          </div>
        )}

        {rawView ? (
          <pre className="bg-black text-green-400 p-4 rounded-lg overflow-auto max-h-[400px] text-xs font-mono">
            {JSON.stringify(digest, null, 2)}
          </pre>
        ) : (
          <>
            {digest?.marketSummary && (
              <div className="mb-4 p-3 rounded-lg bg-indigo-900/20 border border-indigo-800/30">
                <p className="text-sm text-indigo-200">{digest.marketSummary}</p>
              </div>
            )}

            {/* Category Filter */}
            {categories.length > 2 && (
              <div className="flex gap-1 flex-wrap mb-3">
                {categories.map(cat => (
                  <button
                    key={cat}
                    onClick={() => setFilter(cat)}
                    className={`px-2 py-1 text-xs rounded-full border transition-colors ${
                      filter === cat
                        ? "bg-indigo-800/30 border-indigo-600/50 text-indigo-300"
                        : "bg-zinc-800/50 border-zinc-700/50 text-zinc-400"
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            )}

            <div className="space-y-2 max-h-[360px] overflow-y-auto">
              {filteredItems.length === 0 ? (
                <p className="text-center text-zinc-500 py-6 text-sm">
                  {loading ? "Loading digest..." : "No digest items available."}
                </p>
              ) : (
                filteredItems.map((item) => (
                  <div key={item.id} className="p-3 rounded-lg bg-zinc-800/50 border border-zinc-700/50">
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <h3 className="text-sm font-medium text-zinc-200">{item.title}</h3>
                      <Badge variant={sentimentVariant(item.sentiment)} size="sm">
                        {item.sentiment}
                      </Badge>
                    </div>
                    <p className="text-xs text-zinc-400 line-clamp-2">{item.summary}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge variant="neutral" size="sm">{item.category}</Badge>
                      <span className="text-xs text-zinc-600">{item.source}</span>
                      <span className="text-xs text-zinc-600 ml-auto">
                        {new Date(item.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </>
        )}

        {digest?.generatedAt && (
          <p className="text-xs text-zinc-600 text-right mt-2">
            Generated: {new Date(digest.generatedAt).toLocaleString()}
          </p>
        )}
      </CardContent>
    </Card>
  );
};

export default DigestPanel;
