
import React, { useState, useEffect, useCallback } from "react"
import { Card, CardContent } from "@/components/ui/card"
import Badge from "@/components/ui/badge"
import Table, { Column } from "@/components/ui/table"
import Progress from "@/components/ui/progress"

interface ArbitrageOpportunity {
  id: string
  pair: string
  exchangeA: string
  exchangeB: string
  priceA: number
  priceB: number
  spread: number
  spreadPercent: number
  volume: number
  estimatedProfit: number
  risk: "low" | "medium" | "high"
  timestamp: string
}

const ArbitragePanel = () => {
  const [log, setLog] = useState("")
  const [opportunities, setOpportunities] = useState<ArbitrageOpportunity[]>([
    { id: "1", pair: "BTC/USDT", exchangeA: "Binance", exchangeB: "Kraken", priceA: 67240, priceB: 67295, spread: 55, spreadPercent: 0.082, volume: 125000, estimatedProfit: 68.75, risk: "low", timestamp: new Date().toISOString() },
    { id: "2", pair: "ETH/USDT", exchangeA: "Coinbase", exchangeB: "Binance", priceA: 3452, priceB: 3461, spread: 9, spreadPercent: 0.26, volume: 85000, estimatedProfit: 221, risk: "medium", timestamp: new Date().toISOString() },
    { id: "3", pair: "SOL/USDT", exchangeA: "Bybit", exchangeB: "OKX", priceA: 177.5, priceB: 178.2, spread: 0.7, spreadPercent: 0.39, volume: 45000, estimatedProfit: 175.5, risk: "low", timestamp: new Date().toISOString() },
  ])
  const [scanning, setScanning] = useState(false)
  const [autoScan, setAutoScan] = useState(false)
  const [totalProfit, setTotalProfit] = useState(0)

  const runArbitrage = useCallback(async () => {
    setScanning(true)
    try {
      const res = await fetch("/api/arbitrage", { method: "POST" })
      const data = await res.json()
      setLog(JSON.stringify(data, null, 2))
      if (data.opportunities) {
        setOpportunities(data.opportunities)
      }
    } catch (err: any) {
      setLog(`Error: ${err.message}`)
    } finally {
      setScanning(false)
    }
  }, [])

  useEffect(() => {
    if (!autoScan) return
    const interval = setInterval(runArbitrage, 10000)
    return () => clearInterval(interval)
  }, [autoScan, runArbitrage])

  useEffect(() => {
    setTotalProfit(opportunities.reduce((sum, o) => sum + o.estimatedProfit, 0))
  }, [opportunities])

  const columns: Column<ArbitrageOpportunity>[] = [
    { key: "pair", label: "Pair", sortable: true },
    { key: "exchangeA", label: "Exchange A" },
    { key: "exchangeB", label: "Exchange B" },
    { key: "priceA", label: "Price A", align: "right", render: (v: number) => `$${v.toLocaleString()}` },
    { key: "priceB", label: "Price B", align: "right", render: (v: number) => `$${v.toLocaleString()}` },
    {
      key: "spreadPercent", label: "Spread %", sortable: true, align: "right",
      render: (v: number) => <span className="text-emerald-400">{v.toFixed(3)}%</span>,
    },
    {
      key: "estimatedProfit", label: "Est. Profit", sortable: true, align: "right",
      render: (v: number) => <span className="text-emerald-400 font-mono">${v.toFixed(2)}</span>,
    },
    {
      key: "risk", label: "Risk",
      render: (v: string) => {
        const m: Record<string, "success" | "warning" | "error"> = { low: "success", medium: "warning", high: "error" }
        return <Badge variant={m[v] || "neutral"} size="sm">{v}</Badge>
      },
    },
  ]

  return (
    <Card className="bg-gradient-to-br from-slate-900 to-purple-950/30 border-purple-800/30">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-white">Omniversal Arbitrage Monitor</h2>
            <p className="text-sm text-zinc-400 mt-1">Cross-exchange spread analysis</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={autoScan ? "success" : "neutral"} dot>{autoScan ? "Auto-Scan" : "Manual"}</Badge>
          </div>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
            <p className="text-xs text-zinc-400">Opportunities</p>
            <p className="text-xl font-bold text-indigo-400">{opportunities.length}</p>
          </div>
          <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
            <p className="text-xs text-zinc-400">Total Est. Profit</p>
            <p className="text-xl font-bold text-emerald-400">${totalProfit.toFixed(2)}</p>
          </div>
          <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
            <p className="text-xs text-zinc-400">Avg Spread</p>
            <p className="text-xl font-bold text-amber-400">
              {(opportunities.reduce((s, o) => s + o.spreadPercent, 0) / (opportunities.length || 1)).toFixed(3)}%
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={runArbitrage}
            disabled={scanning}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg text-sm text-white transition-colors disabled:opacity-50"
          >
            {scanning ? "Scanning..." : "Run Analysis"}
          </button>
          <button
            onClick={() => setAutoScan(!autoScan)}
            className={`px-4 py-2 rounded-lg text-sm transition-colors ${
              autoScan ? "bg-red-700 hover:bg-red-600 text-white" : "bg-zinc-700 hover:bg-zinc-600 text-zinc-300"
            }`}
          >
            {autoScan ? "Stop Auto" : "Start Auto"}
          </button>
        </div>

        {/* Table */}
        <Table columns={columns} data={opportunities} sortable striped />

        {/* Raw Log */}
        {log && (
          <details className="mt-4">
            <summary className="text-xs text-zinc-500 cursor-pointer hover:text-zinc-300">Raw API Response</summary>
            <pre className="mt-2 text-xs bg-black p-3 rounded max-h-40 overflow-y-auto text-green-400 font-mono">
              {log}
            </pre>
          </details>
        )}
      </CardContent>
    </Card>
  )
}

export default ArbitragePanel
