import React, { useState, useEffect } from "react";

interface UniverseScenario {
  id: string;
  name: string;
  description: string;
  btcPrice: number;
  btcChange: number;
  sp500: number;
  inflation: number;
  fedRate: number;
  sentiment: string;
  probability: number;
  color: string;
}

const SCENARIOS: UniverseScenario[] = [
  { id: "base", name: "Base Case", description: "Current trajectory continues. Moderate growth with declining inflation.", btcPrice: 67432, btcChange: 2.1, sp500: 5280, inflation: 3.2, fedRate: 5.25, sentiment: "Neutral", probability: 45, color: "blue" },
  { id: "bull", name: "Bull Run", description: "ETF inflows surge. Halving FOMO kicks in. Risk-on globally.", btcPrice: 95000, btcChange: 41.2, sp500: 5800, inflation: 2.8, fedRate: 4.5, sentiment: "Euphoria", probability: 25, color: "green" },
  { id: "bear", name: "Black Swan", description: "Major exchange collapse. Regulatory crackdown. Credit crisis.", btcPrice: 35000, btcChange: -48.1, sp500: 4200, inflation: 4.5, fedRate: 6.0, sentiment: "Fear", probability: 10, color: "red" },
  { id: "stag", name: "Stagnation", description: "Sideways movement. Low volume. Market indecision.", btcPrice: 62000, btcChange: -8.1, sp500: 5100, inflation: 3.5, fedRate: 5.25, sentiment: "Apathy", probability: 20, color: "yellow" },
];

export default function UniverseMirrorPanel() {
  const [scenarios, setScenarios] = useState(SCENARIOS);
  const [highlighted, setHighlighted] = useState<string | null>(null);

  // Subtle random variation
  useEffect(() => {
    const interval = setInterval(() => {
      setScenarios((prev) =>
        prev.map((s) => ({
          ...s,
          btcPrice: Math.round(s.btcPrice * (1 + (Math.random() - 0.5) * 0.002)),
          sp500: Math.round(s.sp500 * (1 + (Math.random() - 0.5) * 0.001)),
        }))
      );
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const COLOR_MAP: Record<string, { border: string; bg: string; text: string; bar: string }> = {
    blue: { border: "border-blue-700", bg: "bg-blue-900/20", text: "text-blue-300", bar: "bg-blue-500" },
    green: { border: "border-green-700", bg: "bg-green-900/20", text: "text-green-300", bar: "bg-green-500" },
    red: { border: "border-red-700", bg: "bg-red-900/20", text: "text-red-300", bar: "bg-red-500" },
    yellow: { border: "border-yellow-700", bg: "bg-yellow-900/20", text: "text-yellow-300", bar: "bg-yellow-500" },
  };

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-4">
      <h2 className="text-lg font-bold text-fuchsia-300">Universe Mirror</h2>
      <p className="text-xs text-gray-500">Parallel economy scenarios side-by-side</p>

      {/* Probability Distribution */}
      <div className="w-full h-4 bg-gray-800 rounded-full overflow-hidden flex">
        {scenarios.map((s) => {
          const c = COLOR_MAP[s.color];
          return (
            <div
              key={s.id}
              className={`${c.bar} h-full cursor-pointer transition-opacity ${highlighted && highlighted !== s.id ? "opacity-30" : ""}`}
              style={{ width: `${s.probability}%` }}
              onMouseEnter={() => setHighlighted(s.id)}
              onMouseLeave={() => setHighlighted(null)}
              title={`${s.name}: ${s.probability}%`}
            />
          );
        })}
      </div>

      {/* Scenario Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {scenarios.map((scenario) => {
          const c = COLOR_MAP[scenario.color];
          return (
            <div
              key={scenario.id}
              className={`${c.bg} border ${c.border} rounded-lg p-3 transition-all ${highlighted === scenario.id ? "ring-1 ring-white/20" : ""}`}
              onMouseEnter={() => setHighlighted(scenario.id)}
              onMouseLeave={() => setHighlighted(null)}
            >
              <div className="flex items-center justify-between mb-1">
                <span className={`text-sm font-bold ${c.text}`}>{scenario.name}</span>
                <span className="text-xs text-gray-500">{scenario.probability}% prob</span>
              </div>
              <p className="text-[10px] text-gray-400 mb-2">{scenario.description}</p>

              <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[10px]">
                <div>
                  <span className="text-gray-500">BTC</span>
                  <p className="text-gray-300 font-mono">${scenario.btcPrice.toLocaleString()}</p>
                  <span className={scenario.btcChange >= 0 ? "text-green-400" : "text-red-400"}>
                    {scenario.btcChange >= 0 ? "+" : ""}{scenario.btcChange.toFixed(1)}%
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">S&P 500</span>
                  <p className="text-gray-300 font-mono">{scenario.sp500.toLocaleString()}</p>
                </div>
                <div>
                  <span className="text-gray-500">Inflation</span>
                  <p className="text-gray-300 font-mono">{scenario.inflation}%</p>
                </div>
                <div>
                  <span className="text-gray-500">Fed Rate</span>
                  <p className="text-gray-300 font-mono">{scenario.fedRate}%</p>
                </div>
              </div>

              <div className="mt-2 pt-1.5 border-t border-gray-700/50">
                <span className="text-[10px] text-gray-500">Sentiment: </span>
                <span className={`text-[10px] ${c.text}`}>{scenario.sentiment}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
