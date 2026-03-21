import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";

interface MarketData {
  symbol: string;
  price: number;
  change24h: number;
  changePercent: number;
  high24h: number;
  low24h: number;
  volume: number;
  candles: { time: string; open: number; high: number; low: number; close: number; volume: number }[];
}

const SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT", "DOGE/USDT"];
const TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"];

const RealTimeMarketPanel: React.FC = () => {
  const [selectedSymbol, setSelectedSymbol] = useState(SYMBOLS[0]);
  const [timeframe, setTimeframe] = useState("1h");
  const [data, setData] = useState<MarketData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const res = await axios.get("/api/trading/live-data", {
        params: { symbol: selectedSymbol, timeframe },
      });
      setData(res.data);
      setError(null);
    } catch (err: any) {
      setError(err?.response?.data?.error || "Failed to fetch market data");
    } finally {
      setLoading(false);
    }
  }, [selectedSymbol, timeframe]);

  useEffect(() => {
    setLoading(true);
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const formatPrice = (price: number) => {
    if (price >= 1000) return price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (price >= 1) return price.toFixed(4);
    return price.toFixed(6);
  };

  const formatVolume = (vol: number) => {
    if (vol >= 1e9) return (vol / 1e9).toFixed(2) + "B";
    if (vol >= 1e6) return (vol / 1e6).toFixed(2) + "M";
    if (vol >= 1e3) return (vol / 1e3).toFixed(2) + "K";
    return vol.toFixed(2);
  };

  const renderMiniChart = () => {
    const candles = data?.candles || [];
    if (candles.length === 0) return <div className="h-32 flex items-center justify-center text-gray-600 text-xs">No chart data</div>;

    const prices = candles.map((c) => c.close);
    const minP = Math.min(...prices);
    const maxP = Math.max(...prices);
    const range = maxP - minP || 1;
    const width = 100;
    const height = 128;
    const stepX = width / (prices.length - 1 || 1);

    const points = prices.map((p, i) => {
      const x = i * stepX;
      const y = height - ((p - minP) / range) * (height - 16) - 8;
      return `${x},${y}`;
    }).join(" ");

    const fillPoints = `0,${height} ${points} ${width},${height}`;
    const isPositive = prices[prices.length - 1] >= prices[0];
    const strokeColor = isPositive ? "#22c55e" : "#ef4444";
    const fillColor = isPositive ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)";

    return (
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-32" preserveAspectRatio="none">
        <polygon points={fillPoints} fill={fillColor} />
        <polyline points={points} fill="none" stroke={strokeColor} strokeWidth="1.5" />
      </svg>
    );
  };

  const renderVolumeBar = () => {
    const candles = data?.candles || [];
    if (candles.length === 0) return null;
    const volumes = candles.map((c) => c.volume);
    const maxVol = Math.max(...volumes) || 1;
    const barW = 100 / volumes.length;

    return (
      <svg viewBox="0 0 100 24" className="w-full h-6" preserveAspectRatio="none">
        {volumes.map((v, i) => {
          const h = (v / maxVol) * 22;
          return <rect key={i} x={i * barW} y={24 - h} width={barW * 0.8} height={h} fill="rgba(99,102,241,0.5)" />;
        })}
      </svg>
    );
  };

  return (
    <div className="bg-gray-900 text-white rounded-xl border border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold">Market Data</h2>
          <div className="flex items-center gap-1">
            {loading && <span className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />}
            <span className="text-xs text-gray-500">Live</span>
          </div>
        </div>

        {/* Symbol Selector */}
        <div className="flex flex-wrap gap-1">
          {SYMBOLS.map((s) => (
            <button
              key={s}
              onClick={() => setSelectedSymbol(s)}
              className={`px-2 py-1 rounded text-xs font-medium transition ${
                selectedSymbol === s ? "bg-blue-600 text-white" : "bg-gray-700 text-gray-300 hover:bg-gray-600"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <div className="p-4 space-y-4">
        {error && (
          <div className="bg-red-900/40 border border-red-700 text-red-300 px-3 py-2 rounded text-xs">{error}</div>
        )}

        {/* Price Display */}
        <div className="flex items-end justify-between">
          <div>
            <p className="text-3xl font-bold font-mono">
              ${data ? formatPrice(data.price) : "--"}
            </p>
            {data && (
              <p className={`text-sm font-medium ${data.changePercent >= 0 ? "text-green-400" : "text-red-400"}`}>
                {data.changePercent >= 0 ? "+" : ""}{data.changePercent.toFixed(2)}%
                <span className="text-gray-500 ml-2">
                  ({data.change24h >= 0 ? "+" : ""}${formatPrice(Math.abs(data.change24h))})
                </span>
              </p>
            )}
          </div>
          <div className="text-right text-xs text-gray-500 space-y-1">
            <p>H: ${data ? formatPrice(data.high24h) : "--"}</p>
            <p>L: ${data ? formatPrice(data.low24h) : "--"}</p>
            <p>Vol: {data ? formatVolume(data.volume) : "--"}</p>
          </div>
        </div>

        {/* Timeframe Selector */}
        <div className="flex gap-1">
          {TIMEFRAMES.map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`px-2 py-1 rounded text-xs font-medium transition ${
                timeframe === tf ? "bg-indigo-600 text-white" : "bg-gray-800 text-gray-400 hover:bg-gray-700"
              }`}
            >
              {tf}
            </button>
          ))}
        </div>

        {/* Mini Chart */}
        <div className="bg-gray-800 rounded-lg p-2">
          {loading && !data ? (
            <div className="h-32 flex items-center justify-center text-gray-600 text-sm">Loading chart...</div>
          ) : (
            renderMiniChart()
          )}
        </div>

        {/* Volume Bar */}
        <div>
          <p className="text-[10px] text-gray-500 mb-1">Volume</p>
          <div className="bg-gray-800 rounded p-1">
            {renderVolumeBar()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RealTimeMarketPanel;
