import React, { useState, useEffect, useRef } from "react";

type NarrationStyle = "professional" | "casual" | "dramatic" | "technical";

interface NarrationEntry {
  id: string;
  text: string;
  timestamp: string;
  style: NarrationStyle;
}

const STYLE_CONFIG: Record<NarrationStyle, { label: string; color: string; description: string }> = {
  professional: { label: "Professional", color: "text-blue-300", description: "Corporate, formal tone" },
  casual: { label: "Casual", color: "text-green-300", description: "Friendly, conversational" },
  dramatic: { label: "Dramatic", color: "text-red-300", description: "Intense, storytelling" },
  technical: { label: "Technical", color: "text-cyan-300", description: "Precise, data-driven" },
};

export default function NarrationPanel() {
  const [playing, setPlaying] = useState(false);
  const [style, setStyle] = useState<NarrationStyle>("professional");
  const [volume, setVolume] = useState(75);
  const [speed, setSpeed] = useState(1.0);
  const [currentText, setCurrentText] = useState("Markets are showing increased volatility today as BTC approaches the key resistance level at $68,000. Our analysis indicates a 73% probability of a breakout, with strong on-chain metrics supporting the bullish thesis.");
  const [entries, setEntries] = useState<NarrationEntry[]>([
    { id: "1", text: "Portfolio rebalancing complete. New allocation: BTC 35%, ETH 25%, SOL 15%, stables 25%.", timestamp: "17:25", style: "professional" },
    { id: "2", text: "Alert: Unusual volume spike detected on ETH/USDT. 3x average in the last 5 minutes.", timestamp: "17:20", style: "technical" },
    { id: "3", text: "The market stirs with anticipation as whales begin to move. A storm brews on the horizon.", timestamp: "17:15", style: "dramatic" },
  ]);
  const [progress, setProgress] = useState(0);

  // Simulate playback progress
  useEffect(() => {
    if (!playing) return;
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          setPlaying(false);
          return 0;
        }
        return prev + speed * 2;
      });
    }, 100);
    return () => clearInterval(interval);
  }, [playing, speed]);

  const togglePlay = () => {
    if (progress >= 100) setProgress(0);
    setPlaying(!playing);
  };

  const generateNarration = () => {
    const newEntry: NarrationEntry = {
      id: Date.now().toString(),
      text: currentText.slice(0, 80) + "...",
      timestamp: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false }),
      style,
    };
    setEntries((prev) => [newEntry, ...prev].slice(0, 10));
  };

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-4">
      <h2 className="text-lg font-bold text-pink-300">Narration Controls</h2>

      {/* Current Narration Text */}
      <div className="bg-gray-950 border border-gray-800 rounded-lg p-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-500">Current Narration</span>
          <span className={`text-[10px] ${STYLE_CONFIG[style].color}`}>{STYLE_CONFIG[style].label}</span>
        </div>
        <p className="text-sm text-gray-300 leading-relaxed italic">{currentText}</p>

        {/* Progress Bar */}
        <div className="mt-2 w-full h-1.5 bg-gray-700 rounded overflow-hidden">
          <div className="h-full bg-pink-500 rounded transition-all" style={{ width: `${progress}%` }} />
        </div>
      </div>

      {/* Playback Controls */}
      <div className="flex items-center justify-center gap-4">
        <button onClick={() => setProgress(0)} className="text-gray-400 hover:text-gray-200 text-sm">|&lt;</button>
        <button onClick={() => setProgress(Math.max(0, progress - 10))} className="text-gray-400 hover:text-gray-200 text-sm">&lt;&lt;</button>
        <button
          onClick={togglePlay}
          className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${
            playing ? "bg-pink-600 hover:bg-pink-500" : "bg-gray-700 hover:bg-gray-600"
          }`}
        >
          <span className="text-white text-lg ml-0.5">{playing ? "||" : ">"}</span>
        </button>
        <button onClick={() => setProgress(Math.min(100, progress + 10))} className="text-gray-400 hover:text-gray-200 text-sm">&gt;&gt;</button>
        <button onClick={() => { setProgress(100); setPlaying(false); }} className="text-gray-400 hover:text-gray-200 text-sm">&gt;|</button>
      </div>

      {/* Style Selector */}
      <div>
        <span className="text-xs text-gray-400 mb-1.5 block">Narration Style</span>
        <div className="grid grid-cols-4 gap-1.5">
          {(Object.keys(STYLE_CONFIG) as NarrationStyle[]).map((s) => {
            const cfg = STYLE_CONFIG[s];
            return (
              <button
                key={s}
                onClick={() => setStyle(s)}
                className={`p-2 rounded border text-center transition-colors ${
                  style === s ? "border-pink-600 bg-pink-900/20" : "border-gray-700 bg-gray-800 hover:bg-gray-750"
                }`}
              >
                <span className={`text-xs font-medium block ${cfg.color}`}>{cfg.label}</span>
                <span className="text-[9px] text-gray-500">{cfg.description}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Volume & Speed */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-400">Volume</span>
            <span className="text-gray-300">{volume}%</span>
          </div>
          <input
            type="range" min={0} max={100} value={volume} onChange={(e) => setVolume(Number(e.target.value))}
            className="w-full h-1.5 bg-gray-700 rounded appearance-none cursor-pointer accent-pink-500"
          />
        </div>
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-400">Speed</span>
            <span className="text-gray-300">{speed.toFixed(1)}x</span>
          </div>
          <input
            type="range" min={0.5} max={2} step={0.1} value={speed} onChange={(e) => setSpeed(Number(e.target.value))}
            className="w-full h-1.5 bg-gray-700 rounded appearance-none cursor-pointer accent-pink-500"
          />
        </div>
      </div>

      {/* Generate Button */}
      <button onClick={generateNarration} className="w-full px-4 py-2 bg-pink-700 hover:bg-pink-600 text-white text-sm rounded-lg transition-colors">
        Generate Narration
      </button>

      {/* History */}
      {entries.length > 0 && (
        <div>
          <span className="text-xs text-gray-500 mb-1 block">Recent Narrations</span>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {entries.map((entry) => (
              <div
                key={entry.id}
                onClick={() => setCurrentText(entry.text)}
                className="flex items-center gap-2 p-1.5 bg-gray-800 rounded cursor-pointer hover:bg-gray-750 text-[10px]"
              >
                <span className="text-gray-600">{entry.timestamp}</span>
                <span className={STYLE_CONFIG[entry.style].color}>[{entry.style}]</span>
                <span className="text-gray-400 truncate flex-1">{entry.text}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
