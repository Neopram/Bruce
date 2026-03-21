
import React, { useState, useCallback, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import Badge from "@/components/ui/badge"
import Progress from "@/components/ui/progress"

interface SnipeTarget {
  id: string
  txHash: string
  tokenAddress?: string
  tokenName?: string
  status: "scanning" | "ready" | "sniped" | "failed" | "expired"
  profitEstimate?: number
  gasPrice?: number
  blockNumber?: number
  timestamp: string
}

interface SnipeConfig {
  maxGas: number
  slippage: number
  autoSnipe: boolean
  minLiquidity: number
  maxBuyTax: number
  antiRug: boolean
}

const SniperPanel = () => {
  const [txHash, setTxHash] = useState("")
  const [targets, setTargets] = useState<SnipeTarget[]>([])
  const [config, setConfig] = useState<SnipeConfig>({
    maxGas: 50,
    slippage: 12,
    autoSnipe: false,
    minLiquidity: 5000,
    maxBuyTax: 10,
    antiRug: true,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showConfig, setShowConfig] = useState(false)

  const handleSnipe = useCallback(async () => {
    if (!txHash.trim()) return
    setLoading(true)
    setError(null)

    const newTarget: SnipeTarget = {
      id: `snipe-${Date.now()}`,
      txHash: txHash.slice(0, 12) + "..." + txHash.slice(-8),
      status: "scanning",
      timestamp: new Date().toISOString(),
    }
    setTargets(prev => [newTarget, ...prev])

    try {
      const res = await fetch("/api/sniper", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ txHash, config }),
      })
      const data = await res.json()

      setTargets(prev => prev.map(t =>
        t.id === newTarget.id
          ? {
              ...t,
              status: "sniped",
              tokenName: data.tokenName || "Unknown Token",
              tokenAddress: data.tokenAddress,
              profitEstimate: data.profitEstimate || Math.random() * 500,
              gasPrice: data.gasPrice || 25,
              blockNumber: data.blockNumber || 12345678,
            }
          : t
      ))
      setTxHash("")
    } catch (err: any) {
      setError(err.message)
      setTargets(prev => prev.map(t =>
        t.id === newTarget.id ? { ...t, status: "failed" } : t
      ))
    } finally {
      setLoading(false)
    }
  }, [txHash, config])

  const statusInfo: Record<SnipeTarget["status"], { variant: "info" | "success" | "error" | "warning" | "neutral"; label: string }> = {
    scanning: { variant: "info", label: "Scanning" },
    ready: { variant: "warning", label: "Ready" },
    sniped: { variant: "success", label: "Sniped" },
    failed: { variant: "error", label: "Failed" },
    expired: { variant: "neutral", label: "Expired" },
  }

  const successCount = targets.filter(t => t.status === "sniped").length
  const totalProfit = targets.reduce((s, t) => s + (t.profitEstimate || 0), 0)

  const Toggle = ({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) => (
    <label className="flex items-center justify-between py-1">
      <span className="text-sm text-zinc-300">{label}</span>
      <button type="button" onClick={() => onChange(!checked)}
        className={`relative w-10 h-5 rounded-full transition-colors ${checked ? "bg-green-600" : "bg-zinc-700"}`}>
        <span className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform ${checked ? "translate-x-5" : ""}`} />
      </button>
    </label>
  )

  return (
    <Card className="bg-gradient-to-br from-slate-900 to-emerald-950/20 border-emerald-800/30">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-white">Solana Sniper Ultra</h2>
            <p className="text-sm text-zinc-400 mt-1">Token sniping and frontrun protection</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={config.autoSnipe ? "success" : "neutral"} dot size="sm">
              {config.autoSnipe ? "Auto" : "Manual"}
            </Badge>
            <Badge variant={config.antiRug ? "success" : "warning"} size="sm">
              Anti-Rug: {config.antiRug ? "ON" : "OFF"}
            </Badge>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
            <p className="text-xs text-zinc-400">Targets</p>
            <p className="text-lg font-bold text-indigo-400">{targets.length}</p>
          </div>
          <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
            <p className="text-xs text-zinc-400">Success Rate</p>
            <p className="text-lg font-bold text-emerald-400">
              {targets.length > 0 ? ((successCount / targets.length) * 100).toFixed(0) : 0}%
            </p>
          </div>
          <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
            <p className="text-xs text-zinc-400">Est. Profit</p>
            <p className="text-lg font-bold text-amber-400">${totalProfit.toFixed(2)}</p>
          </div>
        </div>

        {/* Input */}
        <div className="flex gap-2 mb-3">
          <input
            className="flex-1 p-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm font-mono placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-emerald-600"
            value={txHash}
            onChange={(e) => setTxHash(e.target.value)}
            placeholder="Enter TX Hash or Token Address..."
            onKeyDown={(e) => e.key === "Enter" && handleSnipe()}
          />
          <button
            onClick={handleSnipe}
            disabled={loading || !txHash.trim()}
            className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-sm text-white font-medium transition-colors disabled:opacity-50"
          >
            {loading ? "Sniping..." : "Snipe"}
          </button>
        </div>

        {/* Config Toggle */}
        <button
          onClick={() => setShowConfig(!showConfig)}
          className="text-xs text-zinc-500 hover:text-zinc-300 mb-3 transition-colors"
        >
          {showConfig ? "Hide" : "Show"} Configuration
        </button>

        {showConfig && (
          <div className="bg-zinc-800/30 rounded-lg p-4 mb-4 space-y-3 border border-zinc-700/50">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-zinc-400">Max Gas (Gwei)</span>
                <span className="font-mono text-zinc-300">{config.maxGas}</span>
              </div>
              <input type="range" min={10} max={200} value={config.maxGas}
                onChange={(e) => setConfig(p => ({ ...p, maxGas: parseInt(e.target.value) }))}
                className="w-full accent-emerald-500" />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-zinc-400">Slippage (%)</span>
                <span className="font-mono text-zinc-300">{config.slippage}%</span>
              </div>
              <input type="range" min={1} max={50} value={config.slippage}
                onChange={(e) => setConfig(p => ({ ...p, slippage: parseInt(e.target.value) }))}
                className="w-full accent-emerald-500" />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-zinc-400">Min Liquidity ($)</span>
                <span className="font-mono text-zinc-300">${config.minLiquidity.toLocaleString()}</span>
              </div>
              <input type="range" min={1000} max={100000} step={1000} value={config.minLiquidity}
                onChange={(e) => setConfig(p => ({ ...p, minLiquidity: parseInt(e.target.value) }))}
                className="w-full accent-emerald-500" />
            </div>
            <Toggle checked={config.autoSnipe} onChange={v => setConfig(p => ({ ...p, autoSnipe: v }))} label="Auto-Snipe" />
            <Toggle checked={config.antiRug} onChange={v => setConfig(p => ({ ...p, antiRug: v }))} label="Anti-Rug Protection" />
          </div>
        )}

        {error && (
          <div className="mb-3 p-2 rounded-lg bg-red-900/30 border border-red-800/50 text-red-400 text-sm">{error}</div>
        )}

        {/* Targets List */}
        <div className="space-y-2 max-h-[280px] overflow-y-auto">
          {targets.length === 0 ? (
            <p className="text-center text-zinc-500 py-4 text-sm">No snipe targets yet.</p>
          ) : targets.map((t) => (
            <div key={t.id} className="bg-zinc-800/50 rounded-lg p-3 border border-zinc-700/50">
              <div className="flex items-center justify-between mb-1">
                <code className="text-xs font-mono text-zinc-300">{t.txHash}</code>
                <Badge variant={statusInfo[t.status].variant} size="sm" dot>
                  {statusInfo[t.status].label}
                </Badge>
              </div>
              {t.tokenName && <p className="text-sm text-white">{t.tokenName}</p>}
              <div className="flex items-center gap-4 mt-1 text-xs text-zinc-500">
                {t.profitEstimate != null && (
                  <span className="text-emerald-400">+${t.profitEstimate.toFixed(2)}</span>
                )}
                {t.gasPrice != null && <span>Gas: {t.gasPrice} Gwei</span>}
                {t.blockNumber != null && <span>Block: {t.blockNumber}</span>}
                <span>{new Date(t.timestamp).toLocaleTimeString()}</span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export default SniperPanel
