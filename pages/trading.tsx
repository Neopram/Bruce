import React, { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import Badge from "@/components/ui/badge";
import Table, { Column } from "@/components/ui/table";
import Tabs from "@/components/ui/tabs";
import Progress from "@/components/ui/progress";
import type { Position, Order, Signal } from "@/types/trading";

const mockPositions: Position[] = [
  {
    id: "pos-1", symbol: "BTC/USDT", side: "buy", entryPrice: 65000, currentPrice: 67245,
    quantity: 0.5, unrealizedPnl: 1122.5, realizedPnl: 0, openedAt: new Date().toISOString(),
  },
  {
    id: "pos-2", symbol: "ETH/USDT", side: "buy", entryPrice: 3500, currentPrice: 3456,
    quantity: 5, unrealizedPnl: -220, realizedPnl: 0, openedAt: new Date().toISOString(),
  },
  {
    id: "pos-3", symbol: "SOL/USDT", side: "sell", entryPrice: 170, currentPrice: 178,
    quantity: 50, unrealizedPnl: -400, realizedPnl: 0, openedAt: new Date().toISOString(),
  },
];

const mockOrders: Order[] = [
  {
    id: "ord-1", symbol: "BTC/USDT", side: "buy", type: "limit", status: "open",
    price: 64000, quantity: 0.25, filledQuantity: 0, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(),
  },
  {
    id: "ord-2", symbol: "ETH/USDT", side: "sell", type: "stop", status: "pending",
    price: 3300, quantity: 3, filledQuantity: 0, stopPrice: 3300, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(),
  },
];

const mockSignals: Signal[] = [
  { id: "sig-1", symbol: "BTC/USDT", action: "buy", confidence: 0.87, source: "momentum", reason: "Breakout above 67k resistance", targetPrice: 72000, stopLoss: 64500, timestamp: new Date().toISOString(), active: true },
  { id: "sig-2", symbol: "SOL/USDT", action: "buy", confidence: 0.72, source: "sentiment", reason: "Positive social sentiment surge", targetPrice: 195, timestamp: new Date().toISOString(), active: true },
  { id: "sig-3", symbol: "AVAX/USDT", action: "sell", confidence: 0.65, source: "mean_reversion", reason: "Overbought RSI on 4h", targetPrice: 28, stopLoss: 38, timestamp: new Date().toISOString(), active: false },
];

const positionColumns: Column<Position>[] = [
  { key: "symbol", label: "Symbol", sortable: true },
  {
    key: "side", label: "Side",
    render: (val: string) => (
      <Badge variant={val === "buy" ? "success" : "error"} size="sm">
        {val.toUpperCase()}
      </Badge>
    ),
  },
  { key: "entryPrice", label: "Entry", sortable: true, render: (v: number) => `$${v.toLocaleString()}`, align: "right" },
  { key: "currentPrice", label: "Current", sortable: true, render: (v: number) => `$${v.toLocaleString()}`, align: "right" },
  { key: "quantity", label: "Qty", align: "right" },
  {
    key: "unrealizedPnl", label: "Unrealized PnL", sortable: true, align: "right",
    render: (v: number) => (
      <span className={v >= 0 ? "text-emerald-400" : "text-red-400"}>
        {v >= 0 ? "+" : ""}${v.toFixed(2)}
      </span>
    ),
  },
];

const orderColumns: Column<Order>[] = [
  { key: "symbol", label: "Symbol" },
  {
    key: "side", label: "Side",
    render: (val: string) => <Badge variant={val === "buy" ? "success" : "error"} size="sm">{val.toUpperCase()}</Badge>,
  },
  { key: "type", label: "Type", render: (v: string) => v.replace("_", " ").toUpperCase() },
  {
    key: "status", label: "Status",
    render: (val: string) => {
      const m: Record<string, "info" | "warning" | "success" | "neutral"> = { open: "info", pending: "warning", filled: "success" };
      return <Badge variant={m[val] || "neutral"} size="sm">{val}</Badge>;
    },
  },
  { key: "price", label: "Price", align: "right", render: (v: number) => `$${v.toLocaleString()}` },
  { key: "quantity", label: "Qty", align: "right" },
];

const TradingPage = () => {
  const [positions] = useState<Position[]>(mockPositions);
  const [orders] = useState<Order[]>(mockOrders);
  const [signals] = useState<Signal[]>(mockSignals);

  const totalPnl = positions.reduce((sum, p) => sum + p.unrealizedPnl, 0);

  return (
    <div className="p-6 space-y-6 bg-zinc-950 min-h-screen text-white">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Trading Center</h1>
        <div className="flex items-center gap-3">
          <Badge variant="success" dot>Live</Badge>
          <span className="text-sm text-zinc-400">Last update: {new Date().toLocaleTimeString()}</span>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-4">
            <p className="text-xs text-zinc-400 uppercase">Open Positions</p>
            <p className="text-2xl font-bold mt-1">{positions.length}</p>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-4">
            <p className="text-xs text-zinc-400 uppercase">Total Unrealized PnL</p>
            <p className={`text-2xl font-bold mt-1 ${totalPnl >= 0 ? "text-emerald-400" : "text-red-400"}`}>
              {totalPnl >= 0 ? "+" : ""}${totalPnl.toFixed(2)}
            </p>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-4">
            <p className="text-xs text-zinc-400 uppercase">Pending Orders</p>
            <p className="text-2xl font-bold mt-1">{orders.length}</p>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-4">
            <p className="text-xs text-zinc-400 uppercase">Active Signals</p>
            <p className="text-2xl font-bold mt-1 text-indigo-400">{signals.filter((s) => s.active).length}</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs
        variant="pills"
        tabs={[
          {
            label: "Positions",
            content: (
              <Card className="bg-zinc-900 border-zinc-800">
                <CardContent className="p-4">
                  <Table columns={positionColumns} data={positions} sortable striped />
                </CardContent>
              </Card>
            ),
          },
          {
            label: "Orders",
            content: (
              <Card className="bg-zinc-900 border-zinc-800">
                <CardContent className="p-4">
                  <Table columns={orderColumns} data={orders} sortable striped />
                </CardContent>
              </Card>
            ),
          },
          {
            label: "Signals",
            content: (
              <Card className="bg-zinc-900 border-zinc-800">
                <CardContent className="p-4">
                  <div className="space-y-3">
                    {signals.map((signal) => (
                      <div key={signal.id} className="flex items-center gap-4 p-3 rounded-lg bg-zinc-800/50 border border-zinc-700/50">
                        <Badge variant={signal.action === "buy" ? "success" : "error"}>
                          {signal.action.toUpperCase()}
                        </Badge>
                        <div className="flex-1">
                          <p className="font-medium">{signal.symbol}</p>
                          <p className="text-sm text-zinc-400">{signal.reason}</p>
                        </div>
                        <div className="text-right">
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-zinc-400">Confidence:</span>
                            <Progress value={signal.confidence * 100} size="sm" variant="info" className="w-20" />
                            <span className="text-sm font-mono">{(signal.confidence * 100).toFixed(0)}%</span>
                          </div>
                          <p className="text-xs text-zinc-500 mt-1">{signal.source}</p>
                        </div>
                        <Badge variant={signal.active ? "success" : "neutral"} size="sm">
                          {signal.active ? "Active" : "Inactive"}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ),
          },
          {
            label: "Strategy View",
            content: (
              <Card className="bg-zinc-900 border-zinc-800">
                <CardContent className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[
                      { name: "Momentum Alpha", winRate: 68, trades: 142, ret: 23.4, status: "active" },
                      { name: "Mean Reversion", winRate: 55, trades: 89, ret: 8.7, status: "active" },
                      { name: "Arbitrage Scanner", winRate: 82, trades: 312, ret: 15.2, status: "active" },
                      { name: "Sentiment Trader", winRate: 61, trades: 67, ret: -2.1, status: "paused" },
                    ].map((strat) => (
                      <div key={strat.name} className="p-4 rounded-lg bg-zinc-800/50 border border-zinc-700/50">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-medium">{strat.name}</h3>
                          <Badge variant={strat.status === "active" ? "success" : "warning"} size="sm">{strat.status}</Badge>
                        </div>
                        <div className="grid grid-cols-3 gap-2 text-sm">
                          <div>
                            <p className="text-zinc-400">Win Rate</p>
                            <p className="font-mono">{strat.winRate}%</p>
                          </div>
                          <div>
                            <p className="text-zinc-400">Trades</p>
                            <p className="font-mono">{strat.trades}</p>
                          </div>
                          <div>
                            <p className="text-zinc-400">Return</p>
                            <p className={`font-mono ${strat.ret >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                              {strat.ret >= 0 ? "+" : ""}{strat.ret}%
                            </p>
                          </div>
                        </div>
                        <Progress value={strat.winRate} variant={strat.winRate >= 60 ? "success" : "warning"} size="sm" className="mt-3" />
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ),
          },
        ]}
      />
    </div>
  );
};

export default TradingPage;
