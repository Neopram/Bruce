import React, { useState, useEffect, useRef } from "react";

interface BiometricData {
  heartRate: number;
  stressLevel: number;
  focusScore: number;
  energyLevel: number;
}

function GaugeChart({ value, max, label, color, unit }: { value: number; max: number; label: string; color: string; unit: string }) {
  const pct = Math.min((value / max) * 100, 100);
  const circumference = 2 * Math.PI * 36;
  const offset = circumference - (pct / 100) * circumference * 0.75; // 270 deg arc

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-24 h-24">
        <svg viewBox="0 0 80 80" className="w-full h-full -rotate-[135deg]">
          <circle cx="40" cy="40" r="36" fill="none" stroke="#374151" strokeWidth="6" strokeDasharray={`${circumference * 0.75} ${circumference * 0.25}`} strokeLinecap="round" />
          <circle cx="40" cy="40" r="36" fill="none" stroke={color} strokeWidth="6" strokeDasharray={`${circumference * 0.75} ${circumference * 0.25}`} strokeDashoffset={offset} strokeLinecap="round" className="transition-all duration-500" />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-lg font-bold text-gray-200">{value}</span>
          <span className="text-[10px] text-gray-500">{unit}</span>
        </div>
      </div>
      <span className="text-xs text-gray-400 mt-1">{label}</span>
    </div>
  );
}

function WaveAnimation({ color, speed }: { color: string; speed: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let frame = 0;
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.beginPath();
      for (let x = 0; x < canvas.width; x++) {
        const y = canvas.height / 2 + Math.sin((x + frame * speed) * 0.05) * 10 + Math.sin((x + frame * speed * 0.7) * 0.08) * 5;
        x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.stroke();
      frame++;
      requestAnimationFrame(animate);
    };
    const id = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(id);
  }, [color, speed]);

  return <canvas ref={canvasRef} width={200} height={40} className="w-full h-10 opacity-60" />;
}

export default function BiometricHUD() {
  const [data, setData] = useState<BiometricData>({
    heartRate: 72,
    stressLevel: 35,
    focusScore: 78,
    energyLevel: 65,
  });

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setData((prev) => ({
        heartRate: Math.max(55, Math.min(120, prev.heartRate + (Math.random() - 0.5) * 4)),
        stressLevel: Math.max(0, Math.min(100, prev.stressLevel + (Math.random() - 0.5) * 6)),
        focusScore: Math.max(0, Math.min(100, prev.focusScore + (Math.random() - 0.5) * 3)),
        energyLevel: Math.max(0, Math.min(100, prev.energyLevel + (Math.random() - 0.48) * 2)),
      }));
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  const hrColor = data.heartRate > 100 ? "#ef4444" : data.heartRate > 85 ? "#f59e0b" : "#34d399";
  const stressColor = data.stressLevel > 70 ? "#ef4444" : data.stressLevel > 40 ? "#f59e0b" : "#34d399";

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-emerald-300">Biometric HUD</h2>
        <span className="flex items-center gap-1 text-xs text-green-400">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          LIVE
        </span>
      </div>

      {/* Heart Rate Wave */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-gray-400">Heart Rate</span>
          <span className="text-sm font-bold" style={{ color: hrColor }}>{Math.round(data.heartRate)} BPM</span>
        </div>
        <WaveAnimation color={hrColor} speed={data.heartRate / 30} />
      </div>

      {/* Gauges */}
      <div className="grid grid-cols-3 gap-2">
        <GaugeChart value={Math.round(data.stressLevel)} max={100} label="Stress" color={stressColor} unit="%" />
        <GaugeChart value={Math.round(data.focusScore)} max={100} label="Focus" color="#8b5cf6" unit="%" />
        <GaugeChart value={Math.round(data.energyLevel)} max={100} label="Energy" color="#06b6d4" unit="%" />
      </div>

      {/* Status Summary */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-gray-800 rounded p-2 border border-gray-700">
          <span className="text-gray-500">Cognitive State</span>
          <p className={`font-semibold mt-0.5 ${data.focusScore > 60 ? "text-green-400" : "text-yellow-400"}`}>
            {data.focusScore > 80 ? "Peak Performance" : data.focusScore > 60 ? "Focused" : data.focusScore > 40 ? "Distracted" : "Fatigued"}
          </p>
        </div>
        <div className="bg-gray-800 rounded p-2 border border-gray-700">
          <span className="text-gray-500">Recommendation</span>
          <p className={`font-semibold mt-0.5 ${data.stressLevel < 50 ? "text-green-400" : "text-red-400"}`}>
            {data.stressLevel > 70 ? "Take a break" : data.stressLevel > 40 ? "Monitor stress" : "Optimal for trading"}
          </p>
        </div>
      </div>

      <p className="text-[10px] text-gray-600 text-center">Simulated biometric data for demonstration</p>
    </div>
  );
}
