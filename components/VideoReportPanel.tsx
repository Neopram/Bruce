import React, { useState, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface VideoReport {
  id: string;
  title: string;
  duration: string;
  createdAt: string;
  status: "ready" | "processing" | "error";
  thumbnailColor: string;
}

export default function VideoReportPanel() {
  const [reports, setReports] = useState<VideoReport[]>([
    { id: "1", title: "Weekly Market Overview - BTC Analysis", duration: "5:32", createdAt: "2024-03-15", status: "ready", thumbnailColor: "from-blue-600 to-purple-600" },
    { id: "2", title: "Risk Assessment Report - Q1 2024", duration: "3:18", createdAt: "2024-03-12", status: "ready", thumbnailColor: "from-green-600 to-cyan-600" },
    { id: "3", title: "Portfolio Performance Summary", duration: "4:45", createdAt: "2024-03-08", status: "ready", thumbnailColor: "from-orange-600 to-red-600" },
  ]);
  const [selected, setSelected] = useState<VideoReport | null>(null);
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [generating, setGenerating] = useState(false);

  const generateReport = async () => {
    setGenerating(true);
    try {
      await fetch(`${API_URL}/api/report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: "market_overview" }),
      });
    } catch { /* proceed */ }

    const newReport: VideoReport = {
      id: Date.now().toString(),
      title: "New Report - " + new Date().toLocaleDateString(),
      duration: "0:00",
      createdAt: new Date().toISOString().slice(0, 10),
      status: "processing",
      thumbnailColor: "from-violet-600 to-fuchsia-600",
    };
    setReports((prev) => [newReport, ...prev]);

    setTimeout(() => {
      setReports((prev) =>
        prev.map((r) => r.id === newReport.id ? { ...r, status: "ready" as const, duration: "3:42" } : r)
      );
      setGenerating(false);
    }, 3000);
  };

  const togglePlay = () => {
    if (!selected) return;
    setPlaying(!playing);
    if (!playing) {
      const interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 100) { clearInterval(interval); setPlaying(false); return 0; }
          return prev + 1;
        });
      }, 200);
    }
  };

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-violet-300">Video Reports</h2>
        <button
          onClick={generateReport}
          disabled={generating}
          className="text-xs px-3 py-1.5 bg-violet-700 hover:bg-violet-600 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded"
        >
          {generating ? "Generating..." : "Generate Report"}
        </button>
      </div>

      {/* Player Area */}
      {selected && (
        <div className="bg-gray-950 border border-gray-800 rounded-lg overflow-hidden">
          <div className={`h-40 bg-gradient-to-br ${selected.thumbnailColor} flex items-center justify-center relative`}>
            <button onClick={togglePlay} className="w-16 h-16 rounded-full bg-black/50 flex items-center justify-center hover:bg-black/70 transition-colors">
              <span className="text-white text-2xl ml-1">{playing ? "||" : ">"}</span>
            </button>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-800">
              <div className="h-full bg-violet-500 transition-all" style={{ width: `${progress}%` }} />
            </div>
          </div>
          <div className="p-3">
            <p className="text-sm text-gray-200">{selected.title}</p>
            <div className="flex items-center gap-3 mt-1 text-[10px] text-gray-500">
              <span>{selected.duration}</span>
              <span>{selected.createdAt}</span>
              <div className="flex-1" />
              <button onClick={() => setProgress(Math.max(0, progress - 10))} className="hover:text-gray-300">-10s</button>
              <button onClick={togglePlay} className="hover:text-gray-300">{playing ? "Pause" : "Play"}</button>
              <button onClick={() => setProgress(Math.min(100, progress + 10))} className="hover:text-gray-300">+10s</button>
            </div>
          </div>
        </div>
      )}

      {/* Video List */}
      <div className="space-y-2">
        {reports.map((report) => (
          <div
            key={report.id}
            onClick={() => { setSelected(report); setProgress(0); setPlaying(false); }}
            className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer border transition-colors ${
              selected?.id === report.id ? "border-violet-600 bg-violet-900/20" : "border-gray-700 bg-gray-800 hover:bg-gray-750"
            }`}
          >
            <div className={`w-16 h-10 rounded bg-gradient-to-br ${report.thumbnailColor} flex items-center justify-center shrink-0`}>
              <span className="text-white text-xs">{">"}</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-200 truncate">{report.title}</p>
              <div className="flex items-center gap-2 text-[10px] text-gray-500">
                <span>{report.duration}</span>
                <span>{report.createdAt}</span>
              </div>
            </div>
            <span className={`text-[10px] px-1.5 py-0.5 rounded ${
              report.status === "ready" ? "bg-green-900 text-green-300" : report.status === "processing" ? "bg-yellow-900 text-yellow-300 animate-pulse" : "bg-red-900 text-red-300"
            }`}>
              {report.status.toUpperCase()}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
