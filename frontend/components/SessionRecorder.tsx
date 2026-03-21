import React, { useState, useEffect, useRef } from "react";

interface SessionEvent {
  id: string;
  timestamp: number;
  type: "click" | "input" | "navigate" | "api_call" | "decision";
  description: string;
}

export default function SessionRecorder() {
  const [recording, setRecording] = useState(false);
  const [events, setEvents] = useState<SessionEvent[]>([]);
  const [elapsed, setElapsed] = useState(0);
  const [replaying, setReplaying] = useState(false);
  const [replayIndex, setReplayIndex] = useState(0);
  const startTimeRef = useRef<number>(0);

  useEffect(() => {
    if (!recording) return;
    const timer = setInterval(() => setElapsed((p) => p + 1), 1000);
    return () => clearInterval(timer);
  }, [recording]);

  const startRecording = () => {
    setRecording(true);
    setEvents([]);
    setElapsed(0);
    startTimeRef.current = Date.now();

    // Simulate events
    const types: SessionEvent["type"][] = ["click", "input", "navigate", "api_call", "decision"];
    const descs = [
      "Opened trading panel",
      "Entered BTC/USDT pair",
      "Navigated to portfolio view",
      "API: GET /bruce-api/emotion/state",
      "Decision: Long BTC at $67,400",
      "Adjusted stop-loss to $66,800",
      "Clicked refresh on market data",
      "API: POST /api/v1/trading/order",
      "Reviewed risk assessment",
      "Navigated to AI logs",
    ];
    let count = 0;
    const interval = setInterval(() => {
      if (count >= 10) { clearInterval(interval); return; }
      setEvents((prev) => [...prev, {
        id: `evt-${Date.now()}`,
        timestamp: Date.now() - startTimeRef.current,
        type: types[Math.floor(Math.random() * types.length)],
        description: descs[count],
      }]);
      count++;
    }, 2000 + Math.random() * 3000);

    return () => clearInterval(interval);
  };

  const stopRecording = () => {
    setRecording(false);
  };

  const startReplay = () => {
    if (events.length === 0) return;
    setReplaying(true);
    setReplayIndex(0);
    const interval = setInterval(() => {
      setReplayIndex((prev) => {
        if (prev >= events.length - 1) {
          clearInterval(interval);
          setReplaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, 800);
  };

  const exportSession = () => {
    const data = JSON.stringify({ events, duration: elapsed, exportedAt: new Date().toISOString() }, null, 2);
    const blob = new Blob([data], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `session_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const formatTime = (ms: number) => {
    const s = Math.floor(ms / 1000);
    const m = Math.floor(s / 60);
    return `${m}:${(s % 60).toString().padStart(2, "0")}`;
  };

  const TYPE_COLORS: Record<string, string> = {
    click: "bg-blue-900 text-blue-300",
    input: "bg-green-900 text-green-300",
    navigate: "bg-yellow-900 text-yellow-300",
    api_call: "bg-cyan-900 text-cyan-300",
    decision: "bg-purple-900 text-purple-300",
  };

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-rose-300">Session Recorder</h2>
        {recording && (
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            <span className="text-xs text-red-400 font-mono">REC {Math.floor(elapsed / 60)}:{(elapsed % 60).toString().padStart(2, "0")}</span>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="flex gap-2">
        {!recording ? (
          <button onClick={startRecording} className="flex-1 px-4 py-2 bg-red-700 hover:bg-red-600 text-white text-sm rounded-lg">
            Start Recording
          </button>
        ) : (
          <button onClick={stopRecording} className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg">
            Stop Recording
          </button>
        )}
        <button
          onClick={startReplay}
          disabled={events.length === 0 || recording || replaying}
          className="px-4 py-2 bg-blue-700 hover:bg-blue-600 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm rounded-lg"
        >
          {replaying ? "Replaying..." : "Replay"}
        </button>
        <button
          onClick={exportSession}
          disabled={events.length === 0}
          className="px-4 py-2 bg-green-700 hover:bg-green-600 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm rounded-lg"
        >
          Export
        </button>
      </div>

      {/* Timeline */}
      {events.length > 0 && (
        <div>
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Timeline ({events.length} events)</span>
            {replaying && <span className="text-blue-400">Replaying: {replayIndex + 1}/{events.length}</span>}
          </div>
          <div className="w-full h-2 bg-gray-700 rounded overflow-hidden mb-3">
            <div
              className="h-full bg-rose-500 rounded transition-all"
              style={{ width: replaying ? `${((replayIndex + 1) / events.length) * 100}%` : "100%" }}
            />
          </div>

          <div className="space-y-1 max-h-52 overflow-y-auto">
            {events.map((evt, i) => (
              <div
                key={evt.id}
                className={`flex items-center gap-2 px-2 py-1.5 rounded text-xs transition-colors ${
                  replaying && i === replayIndex ? "bg-gray-800 ring-1 ring-rose-500/50" : "bg-gray-800/50"
                }`}
              >
                <span className="text-gray-600 font-mono w-10 shrink-0">{formatTime(evt.timestamp)}</span>
                <span className={`text-[9px] px-1.5 py-0.5 rounded shrink-0 ${TYPE_COLORS[evt.type]}`}>{evt.type}</span>
                <span className="text-gray-300 truncate">{evt.description}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {events.length === 0 && !recording && (
        <p className="text-gray-600 text-sm text-center py-6">Start recording to capture session events</p>
      )}
    </div>
  );
}
