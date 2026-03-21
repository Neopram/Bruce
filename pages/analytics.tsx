import React, { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import Badge from "@/components/ui/badge";
import Tabs from "@/components/ui/tabs";
import ChartWrapper from "@/components/ui/chart-wrapper";
import Table, { Column } from "@/components/ui/table";
import Progress from "@/components/ui/progress";
import { EmotionType } from "@/types/emotion";

const emotionTrendData = [
  { time: "00:00", focused: 70, alert: 30, confident: 50, calm: 80 },
  { time: "04:00", focused: 65, alert: 45, confident: 55, calm: 60 },
  { time: "08:00", focused: 80, alert: 60, confident: 70, calm: 40 },
  { time: "12:00", focused: 90, alert: 35, confident: 85, calm: 55 },
  { time: "16:00", focused: 75, alert: 50, confident: 60, calm: 65 },
  { time: "20:00", focused: 60, alert: 25, confident: 45, calm: 85 },
];

const performanceData = [
  { month: "Oct", pnl: 2400, trades: 45, winRate: 62 },
  { month: "Nov", pnl: -800, trades: 38, winRate: 47 },
  { month: "Dec", pnl: 5200, trades: 52, winRate: 71 },
  { month: "Jan", pnl: 3100, trades: 41, winRate: 65 },
  { month: "Feb", pnl: 7800, trades: 67, winRate: 73 },
  { month: "Mar", pnl: 4500, trades: 53, winRate: 68 },
];

const backtestResults = [
  { strategy: "Momentum Alpha", period: "90d", trades: 342, winRate: 67.5, sharpe: 1.82, maxDD: -8.3, totalReturn: 23.4 },
  { strategy: "Mean Reversion", period: "90d", trades: 218, winRate: 54.1, sharpe: 1.21, maxDD: -12.7, totalReturn: 8.7 },
  { strategy: "Arbitrage Scanner", period: "90d", trades: 891, winRate: 81.2, sharpe: 2.45, maxDD: -3.1, totalReturn: 15.2 },
  { strategy: "Trend Following", period: "90d", trades: 156, winRate: 42.3, sharpe: 0.98, maxDD: -15.6, totalReturn: 11.8 },
  { strategy: "Scalper Bot", period: "90d", trades: 2104, winRate: 58.7, sharpe: 1.55, maxDD: -5.4, totalReturn: 19.1 },
];

const allocationData = [
  { name: "BTC", value: 45 },
  { name: "ETH", value: 25 },
  { name: "SOL", value: 15 },
  { name: "USDT", value: 10 },
  { name: "Other", value: 5 },
];

const backtestColumns: Column[] = [
  { key: "strategy", label: "Strategy", sortable: true },
  { key: "period", label: "Period" },
  { key: "trades", label: "Trades", sortable: true, align: "right" },
  {
    key: "winRate", label: "Win Rate", sortable: true, align: "right",
    render: (v: number) => (
      <span className={v >= 60 ? "text-emerald-400" : v >= 50 ? "text-amber-400" : "text-red-400"}>
        {v}%
      </span>
    ),
  },
  { key: "sharpe", label: "Sharpe", sortable: true, align: "right", render: (v: number) => v.toFixed(2) },
  {
    key: "maxDD", label: "Max DD", sortable: true, align: "right",
    render: (v: number) => <span className="text-red-400">{v}%</span>,
  },
  {
    key: "totalReturn", label: "Return", sortable: true, align: "right",
    render: (v: number) => <span className={v >= 0 ? "text-emerald-400" : "text-red-400"}>+{v}%</span>,
  },
];

const AnalyticsPage = () => {
  const [selectedPeriod, setSelectedPeriod] = useState("90d");

  return (
    <div className="p-6 space-y-6 bg-zinc-950 min-h-screen text-white">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Analytics</h1>
        <div className="flex items-center gap-2">
          {["7d", "30d", "90d", "1y", "All"].map((period) => (
            <button
              key={period}
              onClick={() => setSelectedPeriod(period)}
              className={`px-3 py-1 text-sm rounded-lg transition-colors ${
                selectedPeriod === period
                  ? "bg-indigo-600 text-white"
                  : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700"
              }`}
            >
              {period}
            </button>
          ))}
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {[
          { label: "Total PnL", value: "$22,200", color: "text-emerald-400" },
          { label: "Win Rate", value: "64.3%", color: "text-blue-400" },
          { label: "Sharpe Ratio", value: "1.67", color: "text-indigo-400" },
          { label: "Max Drawdown", value: "-15.6%", color: "text-red-400" },
          { label: "Total Trades", value: "296", color: "text-amber-400" },
        ].map((stat) => (
          <Card key={stat.label} className="bg-zinc-900 border-zinc-800">
            <CardContent className="p-4 text-center">
              <p className="text-xs text-zinc-400 uppercase">{stat.label}</p>
              <p className={`text-xl font-bold mt-1 ${stat.color}`}>{stat.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Tabs
        variant="underline"
        tabs={[
          {
            label: "Emotion Trends",
            content: (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <Card className="bg-zinc-900 border-zinc-800 lg:col-span-2">
                  <CardContent className="p-4">
                    <h3 className="text-lg font-semibold mb-4">Emotion Intensity Over Time</h3>
                    <ChartWrapper
                      data={emotionTrendData}
                      type="area"
                      config={{
                        dataKeys: ["focused", "alert", "confident", "calm"],
                        xAxisKey: "time",
                        height: 320,
                        colors: ["#6366f1", "#f59e0b", "#10b981", "#06b6d4"],
                      }}
                    />
                  </CardContent>
                </Card>
                <Card className="bg-zinc-900 border-zinc-800">
                  <CardContent className="p-4">
                    <h3 className="text-lg font-semibold mb-4">Current Distribution</h3>
                    <div className="space-y-3">
                      {[
                        { emotion: "Focused", value: 82, variant: "default" as const },
                        { emotion: "Confident", value: 71, variant: "success" as const },
                        { emotion: "Alert", value: 45, variant: "warning" as const },
                        { emotion: "Calm", value: 68, variant: "info" as const },
                        { emotion: "Analytical", value: 90, variant: "default" as const },
                      ].map((item) => (
                        <div key={item.emotion}>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-zinc-300">{item.emotion}</span>
                            <span className="text-zinc-400">{item.value}%</span>
                          </div>
                          <Progress value={item.value} variant={item.variant} size="sm" />
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            ),
          },
          {
            label: "Trading Performance",
            content: (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card className="bg-zinc-900 border-zinc-800">
                  <CardContent className="p-4">
                    <h3 className="text-lg font-semibold mb-4">Monthly PnL</h3>
                    <ChartWrapper
                      data={performanceData}
                      type="bar"
                      config={{
                        dataKeys: ["pnl"],
                        xAxisKey: "month",
                        height: 280,
                        colors: ["#6366f1"],
                      }}
                    />
                  </CardContent>
                </Card>
                <Card className="bg-zinc-900 border-zinc-800">
                  <CardContent className="p-4">
                    <h3 className="text-lg font-semibold mb-4">Portfolio Allocation</h3>
                    <ChartWrapper
                      data={allocationData}
                      type="pie"
                      config={{
                        dataKeys: ["value"],
                        xAxisKey: "name",
                        height: 280,
                        innerRadius: 50,
                        outerRadius: 100,
                      }}
                    />
                  </CardContent>
                </Card>
                <Card className="bg-zinc-900 border-zinc-800 lg:col-span-2">
                  <CardContent className="p-4">
                    <h3 className="text-lg font-semibold mb-4">Win Rate Trend</h3>
                    <ChartWrapper
                      data={performanceData}
                      type="line"
                      config={{
                        dataKeys: ["winRate"],
                        xAxisKey: "month",
                        height: 250,
                        colors: ["#10b981"],
                      }}
                    />
                  </CardContent>
                </Card>
              </div>
            ),
          },
          {
            label: "Backtest Results",
            content: (
              <Card className="bg-zinc-900 border-zinc-800">
                <CardContent className="p-4">
                  <h3 className="text-lg font-semibold mb-4">Strategy Backtesting Summary</h3>
                  <Table columns={backtestColumns} data={backtestResults} sortable striped />
                </CardContent>
              </Card>
            ),
          },
        ]}
      />
    </div>
  );
};

export default AnalyticsPage;
