import React, { useEffect, useState, lazy, Suspense } from "react";
import { Card, CardContent } from "@/components/ui/card";
import Badge from "@/components/ui/badge";
import Progress from "@/components/ui/progress";
import { useEmotion } from "@/hooks/useEmotion";
import { useCognition } from "@/hooks/useCognition";

const CognitiveDashboard = lazy(() => import("@/components/panels/CognitiveDashboard"));
const DigestPanel = lazy(() => import("@/components/panels/DigestPanel"));
const TIAHistoryPanel = lazy(() => import("@/components/panels/TIAHistoryPanel"));

const LoadingFallback = () => (
  <div className="animate-pulse bg-zinc-800/50 rounded-xl h-48 flex items-center justify-center">
    <span className="text-zinc-500 text-sm">Loading panel...</span>
  </div>
);

interface MarketTicker {
  symbol: string;
  price: number;
  change: number;
}

interface AlertItem {
  id: string;
  type: "info" | "warning" | "error" | "success";
  message: string;
  timestamp: string;
}

const DashboardPage = () => {
  const { emotion } = useEmotion();
  const { status: cognitionStatus, loading: cognitionLoading } = useCognition();
  const [marketData, setMarketData] = useState<MarketTicker[]>([
    { symbol: "BTC/USDT", price: 67245.32, change: 2.45 },
    { symbol: "ETH/USDT", price: 3456.78, change: -1.23 },
    { symbol: "SOL/USDT", price: 178.45, change: 5.67 },
    { symbol: "BNB/USDT", price: 612.34, change: 0.89 },
  ]);
  const [alerts, setAlerts] = useState<AlertItem[]>([
    { id: "1", type: "info", message: "Market analysis complete - 3 new signals detected", timestamp: new Date().toISOString() },
    { id: "2", type: "warning", message: "High volatility detected on SOL/USDT", timestamp: new Date().toISOString() },
    { id: "3", type: "success", message: "Strategy #4 achieved 12.3% return this week", timestamp: new Date().toISOString() },
  ]);
  const [portfolioValue, setPortfolioValue] = useState(125430.67);
  const [aiHealth, setAiHealth] = useState(92);

  const alertVariantMap: Record<string, "info" | "warning" | "error" | "success"> = {
    info: "info",
    warning: "warning",
    error: "error",
    success: "success",
  };

  return (
    <div className="p-6 space-y-6 bg-zinc-950 min-h-screen text-white">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Bruce AI Dashboard</h1>
        <div className="flex items-center gap-3">
          <Badge variant="success" dot>System Online</Badge>
          <Badge variant="info">v2.1.0</Badge>
        </div>
      </div>

      {/* Top Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-4">
            <p className="text-xs text-zinc-400 uppercase tracking-wider">Portfolio Value</p>
            <p className="text-2xl font-bold text-emerald-400 mt-1">
              ${portfolioValue.toLocaleString("en-US", { minimumFractionDigits: 2 })}
            </p>
            <p className="text-xs text-emerald-500 mt-1">+3.24% today</p>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-4">
            <p className="text-xs text-zinc-400 uppercase tracking-wider">AI Health</p>
            <div className="mt-2">
              <Progress value={aiHealth} variant="success" size="md" showValue />
            </div>
            <p className="text-xs text-zinc-500 mt-1">All systems operational</p>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-4">
            <p className="text-xs text-zinc-400 uppercase tracking-wider">Active Strategies</p>
            <p className="text-2xl font-bold text-indigo-400 mt-1">7</p>
            <p className="text-xs text-zinc-500 mt-1">3 profitable, 2 neutral, 2 pending</p>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-4">
            <p className="text-xs text-zinc-400 uppercase tracking-wider">Emotional State</p>
            <p className="text-2xl font-bold text-amber-400 mt-1 capitalize">
              {(emotion as any)?.current || "Focused"}
            </p>
            <p className="text-xs text-zinc-500 mt-1">Intensity: {((emotion as any)?.intensity || 0.7) * 100}%</p>
          </CardContent>
        </Card>
      </div>

      {/* Market Overview */}
      <Card className="bg-zinc-900 border-zinc-800">
        <CardContent className="p-4">
          <h2 className="text-lg font-semibold mb-3">Market Overview</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {marketData.map((ticker) => (
              <div key={ticker.symbol} className="bg-zinc-800/50 rounded-lg p-3">
                <p className="text-sm text-zinc-400">{ticker.symbol}</p>
                <p className="text-lg font-mono font-bold">${ticker.price.toLocaleString()}</p>
                <p className={`text-sm font-medium ${ticker.change >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {ticker.change >= 0 ? "+" : ""}{ticker.change}%
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Suspense fallback={<LoadingFallback />}>
            <CognitiveDashboard />
          </Suspense>
          <Suspense fallback={<LoadingFallback />}>
            <DigestPanel />
          </Suspense>
        </div>

        <div className="space-y-6">
          {/* Recent Alerts */}
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="p-4">
              <h2 className="text-lg font-semibold mb-3">Recent Alerts</h2>
              <div className="space-y-2">
                {alerts.map((alert) => (
                  <div key={alert.id} className="flex items-start gap-2 p-2 rounded-lg bg-zinc-800/30">
                    <Badge variant={alertVariantMap[alert.type]} size="sm">
                      {alert.type}
                    </Badge>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-zinc-300">{alert.message}</p>
                      <p className="text-xs text-zinc-500 mt-0.5">
                        {new Date(alert.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Suspense fallback={<LoadingFallback />}>
            <TIAHistoryPanel />
          </Suspense>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
