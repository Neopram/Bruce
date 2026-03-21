import React, { useState, useEffect, useRef } from "react";

interface BrainwaveBand {
  name: string;
  frequency: string;
  value: number;
  color: string;
}

interface CommandMapping {
  signal: string;
  action: string;
  confidence: number;
  active: boolean;
}

export default function NeuralinkSimulationPanel() {
  const [bands, setBands] = useState<BrainwaveBand[]>([
    { name: "Delta", frequency: "0.5-4 Hz", value: 0.2, color: "#ef4444" },
    { name: "Theta", frequency: "4-8 Hz", value: 0.4, color: "#f59e0b" },
    { name: "Alpha", frequency: "8-13 Hz", value: 0.65, color: "#22c55e" },
    { name: "Beta", frequency: "13-30 Hz", value: 0.8, color: "#3b82f6" },
    { name: "Gamma", frequency: "30-100 Hz", value: 0.45, color: "#8b5cf6" },
  ]);

  const [mappings] = useState<CommandMapping[]>([
    { signal: "High Beta + Gamma", action: "Execute Trade", confidence: 0.87, active: true },
    { signal: "Alpha Dominance", action: "Review Portfolio", confidence: 0.72, active: true },
    { signal: "Theta Spike", action: "Pause Trading", confidence: 0.65, active: false },
    { signal: "Beta Suppression", action: "Risk Alert", confidence: 0.91, active: true },
    { signal: "Gamma Burst", action: "Quick Analysis", confidence: 0.78, active: false },
  ]);

  const [connectionStatus, setConnectionStatus] = useState<"connected" | "calibrating" | "disconnected">("calibrating");
  const [signalQuality, setSignalQuality] = useState(78);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Simulate brainwave changes
  useEffect(() => {
    const interval = setInterval(() => {
      setBands((prev) => prev.map((b) => ({
        ...b,
        value: Math.max(0.05, Math.min(1, b.value + (Math.random() - 0.5) * 0.1)),
      })));
      setSignalQuality((prev) => Math.max(50, Math.min(100, prev + (Math.random() - 0.5) * 5)));
    }, 500);

    setTimeout(() => setConnectionStatus("connected"), 2000);

    return () => clearInterval(interval);
  }, []);

  // Brainwave visualization
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let frame = 0;
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      bands.forEach((band, i) => {
        ctx.strokeStyle = band.color;
        ctx.lineWidth = 1.5;
        ctx.globalAlpha = 0.6 + band.value * 0.4;
        ctx.beginPath();
        const yOffset = 15 + i * 25;
        for (let x = 0; x < canvas.width; x++) {
          const freq = (i + 1) * 2;
          const amp = band.value * 10;
          const y = yOffset + Math.sin((x + frame * freq) * 0.04) * amp + Math.sin((x + frame) * 0.02) * 3;
          x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.stroke();
        ctx.globalAlpha = 1;
      });

      frame++;
      requestAnimationFrame(animate);
    };
    const id = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(id);
  }, [bands]);

  const STATUS_COLORS = {
    connected: { text: "text-green-400", dot: "bg-green-500" },
    calibrating: { text: "text-yellow-400", dot: "bg-yellow-500 animate-pulse" },
    disconnected: { text: "text-red-400", dot: "bg-red-500" },
  };

  const sc = STATUS_COLORS[connectionStatus];

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-violet-300">Neuralink Simulation</h2>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${sc.dot}`} />
          <span className={`text-xs ${sc.text}`}>{connectionStatus.toUpperCase()}</span>
        </div>
      </div>

      {/* Brainwave Visualization */}
      <div className="bg-gray-950 border border-gray-800 rounded-lg overflow-hidden">
        <canvas ref={canvasRef} width={400} height={140} className="w-full h-36" />
      </div>

      {/* Signal Quality */}
      <div>
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Signal Quality</span>
          <span className={signalQuality > 75 ? "text-green-400" : signalQuality > 50 ? "text-yellow-400" : "text-red-400"}>
            {signalQuality.toFixed(0)}%
          </span>
        </div>
        <div className="w-full h-2 bg-gray-700 rounded overflow-hidden">
          <div
            className={`h-full rounded transition-all ${signalQuality > 75 ? "bg-green-500" : signalQuality > 50 ? "bg-yellow-500" : "bg-red-500"}`}
            style={{ width: `${signalQuality}%` }}
          />
        </div>
      </div>

      {/* Band Levels */}
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-gray-400">Brainwave Bands</h3>
        {bands.map((band) => (
          <div key={band.name} className="flex items-center gap-2">
            <span className="text-xs text-gray-400 w-14">{band.name}</span>
            <span className="text-[10px] text-gray-600 w-16">{band.frequency}</span>
            <div className="flex-1 h-2 bg-gray-700 rounded overflow-hidden">
              <div className="h-full rounded transition-all" style={{ width: `${band.value * 100}%`, backgroundColor: band.color }} />
            </div>
            <span className="text-[10px] text-gray-400 w-8 text-right">{(band.value * 100).toFixed(0)}%</span>
          </div>
        ))}
      </div>

      {/* Command Mappings */}
      <div>
        <h3 className="text-sm font-semibold text-gray-400 mb-2">Command Mappings</h3>
        <div className="space-y-1">
          {mappings.map((m, i) => (
            <div key={i} className={`flex items-center justify-between p-2 rounded border ${m.active ? "border-violet-700 bg-violet-900/10" : "border-gray-700 bg-gray-800"}`}>
              <div className="flex items-center gap-2">
                <span className={`w-1.5 h-1.5 rounded-full ${m.active ? "bg-violet-400 animate-pulse" : "bg-gray-600"}`} />
                <span className="text-xs text-gray-400">{m.signal}</span>
                <span className="text-xs text-gray-600">-&gt;</span>
                <span className="text-xs text-gray-200">{m.action}</span>
              </div>
              <span className="text-[10px] text-gray-500">{(m.confidence * 100).toFixed(0)}%</span>
            </div>
          ))}
        </div>
      </div>

      <p className="text-[10px] text-gray-600 text-center">Simulated neural signals for demonstration</p>
    </div>
  );
}
