import React, { useState, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import Badge from "@/components/ui/badge";

interface ScrapeResult {
  source: string;
  data: string;
  metadata?: {
    rows?: number;
    timestamp?: string;
    format?: string;
  };
}

const PRESET_SOURCES = [
  { value: "WorldBank", label: "World Bank" },
  { value: "IMF", label: "IMF Reports" },
  { value: "FederalReserve", label: "Federal Reserve" },
  { value: "ECB", label: "ECB Data" },
  { value: "BLS", label: "Bureau of Labor Stats" },
  { value: "CoinGecko", label: "CoinGecko Market" },
];

export default function ScraperConsole() {
  const [source, setSource] = useState("");
  const [customUrl, setCustomUrl] = useState("");
  const [results, setResults] = useState<ScrapeResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"preset" | "custom">("preset");

  const scrape = useCallback(async (target: string) => {
    if (!target.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/vantablack/scrape?source=${encodeURIComponent(target)}`);
      if (!res.ok) throw new Error(`Scrape failed (${res.status})`);
      const data = await res.json();
      const result: ScrapeResult = {
        source: target,
        data: typeof data.data === "string" ? data.data : JSON.stringify(data.data, null, 2),
        metadata: data.metadata,
      };
      setResults((prev) => [result, ...prev].slice(0, 10));
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <Card className="bg-gradient-to-br from-zinc-900 to-yellow-950/20 border-yellow-800/30">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-white">Economic Scraper Console</h2>
          <Badge variant="info" size="sm">{results.length} results</Badge>
        </div>

        {/* Tab Toggle */}
        <div className="flex gap-1 mb-4 bg-zinc-800/50 rounded-lg p-1">
          <button
            onClick={() => setActiveTab("preset")}
            className={`flex-1 px-3 py-1.5 text-sm rounded-md transition-colors ${
              activeTab === "preset" ? "bg-yellow-700/50 text-white" : "text-zinc-400 hover:text-white"
            }`}
          >
            Preset Sources
          </button>
          <button
            onClick={() => setActiveTab("custom")}
            className={`flex-1 px-3 py-1.5 text-sm rounded-md transition-colors ${
              activeTab === "custom" ? "bg-yellow-700/50 text-white" : "text-zinc-400 hover:text-white"
            }`}
          >
            Custom URL
          </button>
        </div>

        {activeTab === "preset" ? (
          <div className="grid grid-cols-2 gap-2 mb-4">
            {PRESET_SOURCES.map((src) => (
              <button
                key={src.value}
                onClick={() => scrape(src.value)}
                disabled={loading}
                className="px-3 py-2 text-sm bg-zinc-800/50 hover:bg-yellow-800/30 border border-zinc-700/50 hover:border-yellow-700/50 rounded-lg transition-all text-left text-zinc-300 disabled:opacity-50"
              >
                {src.label}
              </button>
            ))}
          </div>
        ) : (
          <div className="flex gap-2 mb-4">
            <input
              value={customUrl}
              onChange={(e) => setCustomUrl(e.target.value)}
              placeholder="Enter source URL or identifier..."
              className="flex-1 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-white placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-yellow-600"
              onKeyDown={(e) => e.key === "Enter" && scrape(customUrl)}
            />
            <button
              onClick={() => scrape(customUrl)}
              disabled={loading || !customUrl.trim()}
              className="px-4 py-2 bg-yellow-700 hover:bg-yellow-600 rounded-lg text-sm text-white transition-colors disabled:opacity-50"
            >
              {loading ? "Scraping..." : "Scrape"}
            </button>
          </div>
        )}

        {error && (
          <div className="mb-4 p-2 rounded-lg bg-red-900/30 border border-red-800/50 text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Results */}
        <div className="space-y-3 max-h-[400px] overflow-y-auto">
          {results.length === 0 ? (
            <p className="text-center text-zinc-500 py-6 text-sm">No scrape results yet. Select a source to begin.</p>
          ) : (
            results.map((r, idx) => (
              <div key={idx} className="bg-zinc-800/50 rounded-lg border border-zinc-700/50 overflow-hidden">
                <div className="flex items-center justify-between px-3 py-2 bg-zinc-800/80">
                  <div className="flex items-center gap-2">
                    <Badge variant="success" size="sm">OK</Badge>
                    <span className="text-sm font-medium text-zinc-300">{r.source}</span>
                  </div>
                  {r.metadata?.rows && (
                    <span className="text-xs text-zinc-500">{r.metadata.rows} rows</span>
                  )}
                </div>
                <pre className="p-3 text-xs text-green-400 font-mono overflow-x-auto max-h-32">
                  {r.data}
                </pre>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
