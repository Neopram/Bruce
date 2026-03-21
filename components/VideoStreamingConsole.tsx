import React, { useState, useEffect, useRef } from "react";

type ConnectionStatus = "disconnected" | "connecting" | "connected" | "error";
type Quality = "auto" | "1080p" | "720p" | "480p" | "360p";

export default function VideoStreamingConsole() {
  const [status, setStatus] = useState<ConnectionStatus>("disconnected");
  const [quality, setQuality] = useState<Quality>("auto");
  const [bitrate, setBitrate] = useState(0);
  const [fps, setFps] = useState(0);
  const [viewers, setViewers] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [streamUrl, setStreamUrl] = useState("");
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Simulated stream visualization
  useEffect(() => {
    if (status !== "connected") return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let frame = 0;
    const render = () => {
      ctx.fillStyle = "#0f172a";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Grid
      ctx.strokeStyle = "#1e293b";
      ctx.lineWidth = 0.5;
      for (let x = 0; x < canvas.width; x += 20) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
      }
      for (let y = 0; y < canvas.height; y += 20) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
      }

      // Simulated waveform
      ctx.strokeStyle = "#8b5cf6";
      ctx.lineWidth = 2;
      ctx.beginPath();
      for (let x = 0; x < canvas.width; x++) {
        const y = canvas.height / 2 + Math.sin((x + frame) * 0.03) * 30 + Math.sin((x + frame * 2) * 0.07) * 15;
        x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.stroke();

      // Overlay text
      ctx.fillStyle = "#8b5cf680";
      ctx.font = "10px monospace";
      ctx.fillText(`LIVE | ${quality} | ${bitrate} kbps`, 8, 16);

      frame++;
      requestAnimationFrame(render);
    };
    const id = requestAnimationFrame(render);
    return () => cancelAnimationFrame(id);
  }, [status, quality, bitrate]);

  // Elapsed timer
  useEffect(() => {
    if (status !== "connected") return;
    const timer = setInterval(() => setElapsed((p) => p + 1), 1000);
    return () => clearInterval(timer);
  }, [status]);

  // Simulated metrics
  useEffect(() => {
    if (status !== "connected") return;
    const interval = setInterval(() => {
      setBitrate(Math.floor(2500 + Math.random() * 500));
      setFps(Math.floor(28 + Math.random() * 4));
      setViewers(Math.floor(12 + Math.random() * 5));
    }, 2000);
    return () => clearInterval(interval);
  }, [status]);

  const connect = () => {
    setStatus("connecting");
    setTimeout(() => {
      setStatus("connected");
      setElapsed(0);
    }, 1500);
  };

  const disconnect = () => {
    setStatus("disconnected");
    setElapsed(0);
    setBitrate(0);
    setFps(0);
  };

  const formatTime = (s: number) => {
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;
    return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${sec.toString().padStart(2, "0")}`;
  };

  const STATUS_COLORS: Record<ConnectionStatus, { text: string; dot: string }> = {
    disconnected: { text: "text-gray-400", dot: "bg-gray-500" },
    connecting: { text: "text-yellow-400", dot: "bg-yellow-500 animate-pulse" },
    connected: { text: "text-green-400", dot: "bg-green-500 animate-pulse" },
    error: { text: "text-red-400", dot: "bg-red-500" },
  };

  const sc = STATUS_COLORS[status];

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-violet-300">Video Streaming</h2>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${sc.dot}`} />
          <span className={`text-xs ${sc.text}`}>{status.toUpperCase()}</span>
        </div>
      </div>

      {/* Stream Display */}
      <div className="bg-gray-950 border border-gray-800 rounded-lg overflow-hidden relative">
        <canvas ref={canvasRef} width={400} height={200} className="w-full h-48" />
        {status === "disconnected" && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-950/80">
            <span className="text-gray-500 text-sm">No active stream</span>
          </div>
        )}
        {status === "connecting" && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-950/80">
            <span className="text-yellow-400 text-sm animate-pulse">Connecting...</span>
          </div>
        )}
        {status === "connected" && (
          <div className="absolute top-2 right-2 flex items-center gap-1 bg-red-600 px-2 py-0.5 rounded text-white text-[10px] font-bold">
            LIVE
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="flex gap-2">
        {status !== "connected" ? (
          <button onClick={connect} disabled={status === "connecting"} className="flex-1 px-4 py-2 bg-green-700 hover:bg-green-600 disabled:bg-gray-700 text-white text-sm rounded-lg">
            {status === "connecting" ? "Connecting..." : "Start Stream"}
          </button>
        ) : (
          <button onClick={disconnect} className="flex-1 px-4 py-2 bg-red-700 hover:bg-red-600 text-white text-sm rounded-lg">
            Stop Stream
          </button>
        )}
        <select
          value={quality}
          onChange={(e) => setQuality(e.target.value as Quality)}
          className="bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded px-3 py-2 focus:outline-none"
        >
          {(["auto", "1080p", "720p", "480p", "360p"] as Quality[]).map((q) => (
            <option key={q} value={q}>{q}</option>
          ))}
        </select>
      </div>

      {/* Stream URL */}
      <input
        type="text"
        value={streamUrl}
        onChange={(e) => setStreamUrl(e.target.value)}
        placeholder="rtmp://stream-url or ws://stream-url"
        className="w-full bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded px-3 py-1.5 focus:border-violet-500 focus:outline-none font-mono"
      />

      {/* Metrics */}
      {status === "connected" && (
        <div className="grid grid-cols-4 gap-2">
          <div className="bg-gray-800 rounded p-2 text-center border border-gray-700">
            <span className="text-[10px] text-gray-500">Duration</span>
            <p className="text-sm font-mono text-gray-200">{formatTime(elapsed)}</p>
          </div>
          <div className="bg-gray-800 rounded p-2 text-center border border-gray-700">
            <span className="text-[10px] text-gray-500">Bitrate</span>
            <p className="text-sm font-mono text-gray-200">{bitrate} kbps</p>
          </div>
          <div className="bg-gray-800 rounded p-2 text-center border border-gray-700">
            <span className="text-[10px] text-gray-500">FPS</span>
            <p className="text-sm font-mono text-gray-200">{fps}</p>
          </div>
          <div className="bg-gray-800 rounded p-2 text-center border border-gray-700">
            <span className="text-[10px] text-gray-500">Viewers</span>
            <p className="text-sm font-mono text-gray-200">{viewers}</p>
          </div>
        </div>
      )}
    </div>
  );
}
