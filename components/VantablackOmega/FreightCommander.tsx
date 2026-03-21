
import React, { useState, useCallback } from "react"
import { Card, CardContent } from "@/components/ui/card"
import Badge from "@/components/ui/badge"
import Table, { Column } from "@/components/ui/table"
import Progress from "@/components/ui/progress"

interface FreightTrade {
  id: string
  asset: string
  volume: number
  pricePerUnit: number
  total: number
  route: string
  status: "pending" | "in_transit" | "delivered" | "cancelled"
  timestamp: string
}

const ASSET_PRESETS = [
  { value: "crude_oil", label: "Crude Oil", unit: "barrels", avgPrice: 78.5 },
  { value: "natural_gas", label: "Natural Gas", unit: "MMBtu", avgPrice: 2.85 },
  { value: "gold", label: "Gold", unit: "oz", avgPrice: 2340 },
  { value: "copper", label: "Copper", unit: "tons", avgPrice: 8950 },
  { value: "wheat", label: "Wheat", unit: "bushels", avgPrice: 5.82 },
  { value: "soybeans", label: "Soybeans", unit: "bushels", avgPrice: 12.45 },
]

const FreightCommander = () => {
  const [asset, setAsset] = useState("")
  const [volume, setVolume] = useState(1000)
  const [customAsset, setCustomAsset] = useState("")
  const [trades, setTrades] = useState<FreightTrade[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const selectedPreset = ASSET_PRESETS.find(a => a.value === asset)
  const estimatedTotal = selectedPreset ? volume * selectedPreset.avgPrice : 0

  const handleTrade = useCallback(async () => {
    const assetName = asset || customAsset
    if (!assetName.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetch("/api/freight", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ asset: assetName, volume }),
      })
      const data = await res.json()
      const newTrade: FreightTrade = {
        id: `ft-${Date.now()}`,
        asset: selectedPreset?.label || customAsset || assetName,
        volume,
        pricePerUnit: selectedPreset?.avgPrice || 0,
        total: estimatedTotal || volume * 100,
        route: data.route || "Direct",
        status: "pending",
        timestamp: new Date().toISOString(),
      }
      setTrades(prev => [newTrade, ...prev])

      // Simulate status updates
      setTimeout(() => {
        setTrades(prev => prev.map(t => t.id === newTrade.id ? { ...t, status: "in_transit" } : t))
      }, 3000)
      setTimeout(() => {
        setTrades(prev => prev.map(t => t.id === newTrade.id ? { ...t, status: "delivered" } : t))
      }, 8000)
    } catch (err: any) {
      setError(err.message || "Trade execution failed")
    } finally {
      setLoading(false)
    }
  }, [asset, volume, customAsset, selectedPreset, estimatedTotal])

  const tradeColumns: Column<FreightTrade>[] = [
    { key: "asset", label: "Asset" },
    { key: "volume", label: "Volume", align: "right", render: (v: number) => v.toLocaleString() },
    { key: "pricePerUnit", label: "Price/Unit", align: "right", render: (v: number) => `$${v.toLocaleString()}` },
    { key: "total", label: "Total", align: "right", render: (v: number) => `$${v.toLocaleString()}` },
    { key: "route", label: "Route" },
    {
      key: "status", label: "Status",
      render: (v: string) => {
        const m: Record<string, "warning" | "info" | "success" | "error"> = {
          pending: "warning", in_transit: "info", delivered: "success", cancelled: "error",
        }
        return <Badge variant={m[v] || "neutral"} size="sm" dot>{v.replace("_", " ")}</Badge>
      },
    },
  ]

  const totalVolume = trades.reduce((s, t) => s + t.volume, 0)
  const totalValue = trades.reduce((s, t) => s + t.total, 0)
  const deliveredCount = trades.filter(t => t.status === "delivered").length

  return (
    <Card className="bg-gradient-to-br from-blue-950 to-zinc-900 border-blue-800/30">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-white">Freight Commander</h2>
            <p className="text-sm text-zinc-400 mt-1">Commodity trading and logistics</p>
          </div>
          <Badge variant="info" size="sm">{trades.length} trades</Badge>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="bg-blue-900/30 rounded-lg p-3 text-center">
            <p className="text-xs text-zinc-400">Total Volume</p>
            <p className="text-lg font-bold text-blue-400">{totalVolume.toLocaleString()}</p>
          </div>
          <div className="bg-blue-900/30 rounded-lg p-3 text-center">
            <p className="text-xs text-zinc-400">Total Value</p>
            <p className="text-lg font-bold text-emerald-400">${totalValue.toLocaleString()}</p>
          </div>
          <div className="bg-blue-900/30 rounded-lg p-3 text-center">
            <p className="text-xs text-zinc-400">Delivered</p>
            <p className="text-lg font-bold text-amber-400">{deliveredCount}/{trades.length}</p>
          </div>
        </div>

        {/* Asset Selection */}
        <div className="space-y-3 mb-4">
          <div>
            <label className="text-sm text-zinc-400 block mb-1">Select Asset</label>
            <div className="grid grid-cols-3 gap-2">
              {ASSET_PRESETS.map(a => (
                <button
                  key={a.value}
                  onClick={() => { setAsset(a.value); setCustomAsset(""); }}
                  className={`p-2 text-xs rounded-lg border transition-colors text-left ${
                    asset === a.value
                      ? "bg-blue-800/30 border-blue-600/50 text-white"
                      : "bg-zinc-800/50 border-zinc-700/50 text-zinc-400 hover:border-zinc-600"
                  }`}
                >
                  <p className="font-medium">{a.label}</p>
                  <p className="text-zinc-500">${a.avgPrice}/{a.unit}</p>
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-zinc-500">or custom:</span>
            <input
              value={customAsset}
              onChange={(e) => { setCustomAsset(e.target.value); setAsset(""); }}
              placeholder="Custom asset name..."
              className="flex-1 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-white placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-blue-600"
            />
          </div>

          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-zinc-400">Volume</span>
              <span className="font-mono text-zinc-300">{volume.toLocaleString()} {selectedPreset?.unit || "units"}</span>
            </div>
            <input
              type="range" min={100} max={50000} step={100} value={volume}
              onChange={(e) => setVolume(parseInt(e.target.value))}
              className="w-full accent-blue-500"
            />
          </div>

          {estimatedTotal > 0 && (
            <div className="bg-blue-900/20 rounded-lg p-3 text-center">
              <p className="text-xs text-zinc-400">Estimated Total</p>
              <p className="text-xl font-bold text-white">${estimatedTotal.toLocaleString()}</p>
            </div>
          )}

          <button
            onClick={handleTrade}
            disabled={loading || (!asset && !customAsset.trim())}
            className="w-full px-4 py-2.5 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm text-white font-medium transition-colors disabled:opacity-50"
          >
            {loading ? "Executing..." : "Execute Trade"}
          </button>
        </div>

        {error && (
          <div className="mb-4 p-2 rounded-lg bg-red-900/30 border border-red-800/50 text-red-400 text-sm">{error}</div>
        )}

        {/* Trade History */}
        {trades.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-zinc-400 mb-2">Trade History</h3>
            <Table columns={tradeColumns} data={trades} sortable striped compact />
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default FreightCommander
