import React, { useEffect, useState } from "react"
import { useApi } from "@/services/api"

export default function VantablackDashboard() {
  const { health, meta, prediction, memory, training } = useApi()

  const [status, setStatus] = useState("...")
  const [info, setInfo] = useState<any>(null)
  const [pred, setPred] = useState("...")
  const [summary, setSummary] = useState<any[]>([])
  const [stats, setStats] = useState<any>(null)
  const [logs, setLogs] = useState<string[]>([])

  useEffect(() => {
    health.check().then(res => setStatus(res.status || "error"))
    meta.info().then(setInfo)
    prediction.get().then(res => setPred(res["AI Prediction"]))
    memory.summary().then(setSummary)
    memory.stats().then(setStats)
    training.logs().then(res => setLogs(res.logs || []))
  }, [])

  return (
    <div className="p-6 space-y-6 bg-black text-white min-h-screen font-mono">
      <h1 className="text-4xl font-bold mb-4">🧠 Bruce AI Strategic Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gray-900 rounded-xl p-4 shadow-md">
          <h2 className="text-xl font-semibold">📡 Backend Status</h2>
          <p>Status: <span className="text-green-400 font-bold">{status}</span></p>
          {info && (
            <div className="text-sm mt-2 space-y-1 text-gray-300">
              <p>Version: {info.version}</p>
              <p>Env: {info.environment}</p>
              <p>Uptime: {info.uptime}</p>
            </div>
          )}
        </div>

        <div className="bg-gray-900 rounded-xl p-4 shadow-md">
          <h2 className="text-xl font-semibold">🤖 AI Prediction</h2>
          <p className="text-lg text-yellow-300 mt-2">{pred}</p>
        </div>

        <div className="bg-gray-900 rounded-xl p-4 shadow-md col-span-2">
          <h2 className="text-xl font-semibold">📘 Episodic Memory Summary</h2>
          {summary.length === 0 ? (
            <p className="text-gray-500 italic">No memory yet.</p>
          ) : (
            <ul className="text-sm mt-2 list-disc ml-4">
              {summary.map((item, idx) => (
                <li key={idx}>Ep {item.episode} – 🏆 {item.reward} / 📉 {item.avg_loss_like_signal}</li>
              ))}
            </ul>
          )}
        </div>

        <div className="bg-gray-900 rounded-xl p-4 shadow-md">
          <h2 className="text-xl font-semibold">📊 Training Stats</h2>
          {stats ? (
            <div className="text-sm text-gray-300 space-y-1 mt-2">
              <p>Total Episodes: {stats.total_episodes}</p>
              <p>Avg Reward: {stats.average_reward}</p>
              <p>Avg Loss: {stats.average_loss_signal}</p>
            </div>
          ) : (
            <p className="text-gray-500 italic">Stats not available.</p>
          )}
        </div>

        <div className="bg-gray-900 rounded-xl p-4 shadow-md col-span-2">
          <h2 className="text-xl font-semibold">📜 Training Logs</h2>
          <div className="bg-gray-800 text-xs text-green-400 p-3 h-60 overflow-y-auto whitespace-pre-wrap">
            {logs.length === 0 ? "No logs yet." : logs.map((log, i) => <div key={i}>{log}</div>)}
          </div>
        </div>
      </div>
    </div>
  )
}