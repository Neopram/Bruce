
import React, { useState, useCallback } from "react"
import { Card, CardContent } from "@/components/ui/card"
import Badge from "@/components/ui/badge"
import Progress from "@/components/ui/progress"

interface VectorResult {
  id: string
  content: string
  score: number
  metadata: {
    source?: string
    type?: string
    timestamp?: string
    tokens?: number
  }
}

interface SearchConfig {
  topK: number
  threshold: number
  namespace: string
  includeMetadata: boolean
}

const NAMESPACES = [
  { value: "all", label: "All Knowledge" },
  { value: "trading", label: "Trading Memory" },
  { value: "conversations", label: "Conversations" },
  { value: "market_data", label: "Market Data" },
  { value: "strategies", label: "Strategies" },
  { value: "episodes", label: "Episodes" },
]

const VectorQueryPanel = () => {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<VectorResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [config, setConfig] = useState<SearchConfig>({
    topK: 10,
    threshold: 0.5,
    namespace: "all",
    includeMetadata: true,
  })
  const [showConfig, setShowConfig] = useState(false)
  const [totalSearches, setTotalSearches] = useState(0)
  const [selectedResult, setSelectedResult] = useState<VectorResult | null>(null)

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    setSelectedResult(null)
    try {
      const res = await fetch("/api/vector-search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, ...config }),
      })
      if (!res.ok) throw new Error(`Search failed (${res.status})`)
      const data = await res.json()

      const parsed: VectorResult[] = (data.results || []).map((r: any, i: number) => ({
        id: r.id || `vr-${i}`,
        content: typeof r === "string" ? r : r.content || r.text || JSON.stringify(r),
        score: r.score || 1 - i * 0.08,
        metadata: {
          source: r.source || r.metadata?.source || "vector_db",
          type: r.type || r.metadata?.type || "document",
          timestamp: r.timestamp || r.metadata?.timestamp,
          tokens: r.tokens || r.metadata?.tokens,
        },
      }))

      setResults(parsed)
      setTotalSearches(prev => prev + 1)
    } catch (err: any) {
      setError(err.message)
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [query, config])

  const getScoreColor = (score: number) => {
    if (score >= 0.9) return "text-emerald-400"
    if (score >= 0.7) return "text-blue-400"
    if (score >= 0.5) return "text-amber-400"
    return "text-zinc-500"
  }

  const getScoreVariant = (score: number) => {
    if (score >= 0.9) return "success" as const
    if (score >= 0.7) return "info" as const
    if (score >= 0.5) return "warning" as const
    return "neutral" as const
  }

  return (
    <Card className="bg-gradient-to-br from-black to-cyan-950/20 border-cyan-800/30">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-white">Vector Semantic Search</h2>
            <p className="text-sm text-zinc-400 mt-1">Neural embedding similarity queries</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="info" size="sm">{results.length} results</Badge>
            <Badge variant="neutral" size="sm">{totalSearches} queries</Badge>
          </div>
        </div>

        {/* Search Input */}
        <div className="flex gap-2 mb-3">
          <input
            className="flex-1 p-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-cyan-600"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search knowledge base..."
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          />
          <button
            onClick={handleSearch}
            disabled={loading || !query.trim()}
            className="px-5 py-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg text-sm text-white font-medium transition-colors disabled:opacity-50"
          >
            {loading ? "Searching..." : "Search"}
          </button>
        </div>

        {/* Namespace Selector */}
        <div className="flex gap-1 flex-wrap mb-3">
          {NAMESPACES.map(ns => (
            <button
              key={ns.value}
              onClick={() => setConfig(p => ({ ...p, namespace: ns.value }))}
              className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
                config.namespace === ns.value
                  ? "bg-cyan-800/30 border-cyan-600/50 text-cyan-300"
                  : "bg-zinc-800/50 border-zinc-700/50 text-zinc-400 hover:text-white"
              }`}
            >
              {ns.label}
            </button>
          ))}
        </div>

        {/* Config Toggle */}
        <button
          onClick={() => setShowConfig(!showConfig)}
          className="text-xs text-zinc-500 hover:text-zinc-300 mb-3 transition-colors"
        >
          {showConfig ? "Hide" : "Show"} Search Config
        </button>

        {showConfig && (
          <div className="bg-zinc-800/30 rounded-lg p-4 mb-4 space-y-3 border border-zinc-700/50">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-zinc-400">Top K Results</span>
                <span className="font-mono text-zinc-300">{config.topK}</span>
              </div>
              <input type="range" min={1} max={50} value={config.topK}
                onChange={(e) => setConfig(p => ({ ...p, topK: parseInt(e.target.value) }))}
                className="w-full accent-cyan-500" />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-zinc-400">Min Score Threshold</span>
                <span className="font-mono text-zinc-300">{config.threshold.toFixed(2)}</span>
              </div>
              <input type="range" min={0} max={1} step={0.05} value={config.threshold}
                onChange={(e) => setConfig(p => ({ ...p, threshold: parseFloat(e.target.value) }))}
                className="w-full accent-cyan-500" />
            </div>
          </div>
        )}

        {error && (
          <div className="mb-3 p-2 rounded-lg bg-red-900/30 border border-red-800/50 text-red-400 text-sm">{error}</div>
        )}

        {/* Results */}
        <div className="space-y-2 max-h-[360px] overflow-y-auto">
          {results.length === 0 && !loading ? (
            <p className="text-center text-zinc-500 py-6 text-sm">
              Enter a query to search the vector knowledge base.
            </p>
          ) : (
            results.map((r, idx) => (
              <button
                key={r.id}
                onClick={() => setSelectedResult(selectedResult?.id === r.id ? null : r)}
                className="w-full text-left p-3 rounded-lg bg-zinc-800/50 hover:bg-cyan-900/20 border border-zinc-700/50 hover:border-cyan-700/50 transition-all"
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-zinc-700/50 flex items-center justify-center text-xs font-bold text-zinc-400">
                    {idx + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-zinc-200 line-clamp-2">{r.content}</p>
                    <div className="flex items-center gap-2 mt-1.5">
                      <Badge variant={getScoreVariant(r.score)} size="sm">
                        {(r.score * 100).toFixed(1)}%
                      </Badge>
                      {r.metadata.source && (
                        <Badge variant="neutral" size="sm">{r.metadata.source}</Badge>
                      )}
                      {r.metadata.type && (
                        <span className="text-xs text-zinc-500">{r.metadata.type}</span>
                      )}
                      {r.metadata.tokens && (
                        <span className="text-xs text-zinc-600">{r.metadata.tokens} tokens</span>
                      )}
                    </div>

                    {selectedResult?.id === r.id && (
                      <div className="mt-2 p-2 bg-cyan-900/20 rounded border border-cyan-800/30">
                        <p className="text-xs text-zinc-300 whitespace-pre-wrap">{r.content}</p>
                        <div className="mt-2 flex items-center gap-2">
                          <span className="text-xs text-zinc-500">Score:</span>
                          <Progress value={r.score * 100} variant={getScoreVariant(r.score)} size="sm" className="flex-1 max-w-32" />
                          <span className={`text-xs font-mono ${getScoreColor(r.score)}`}>
                            {(r.score * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export default VectorQueryPanel
