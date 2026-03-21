// Ruta: frontend/components/Dashboard.tsx

import { useEffect, useState } from "react"
import { useApi } from "@/services/useApi"

export default function Dashboard() {
  const { health, prediction, memory, training, meta } = useApi()

  const [status, setStatus] = useState("Loading...")
  const [pred, setPred] = useState("")
  const [logs, setLogs] = useState<string[]>([])
  const [summary, setSummary] = useState<any[]>([])
  const [stats, setStats] = useState<any>(null)
  const [metaInfo, setMetaInfo] = useState<any>(null)

  // Fetch inicial
  useEffect(() => {
    health.general().then(res => setStatus(res.status || "Unknown"))
    prediction.get().then(res => setPred(res["AI Prediction"] || "N/A"))
    memory.summary().then(setSummary)
    memory.stats().then(setStats)
    training.logs().then(res => setLogs(res.logs || []))
    meta.info().then(setMetaInfo)

    // Auto-actualización cada 15s
    const interval = setInterval(() => {
      prediction.get().then(res => setPred(res["AI Prediction"] || "N/A"))
      memory.stats().then(setStats)
    }, 15000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="p-6 space-y-6 font-sans text-gray-800">
      <h1 className="text-3xl font-bold">🧠 Bruce AI – Strategic Dashboard</h1>

      {/* Estado general */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-xl font-semibold">📡 Backend Status</h2>
          <p className="text-sm">Status: <strong>{status}</strong></p>
          {metaInfo && (
            <div className="text-xs mt-2 text-gray-600 space-y-1">
              <p>Version: {metaInfo.version}</p>
              <p>Environment: {metaInfo.environment}</p>
              <p>Uptime: {metaInfo.uptime}</p>
            </div>
          )}
        </div>

        <div className="card">
          <h2 className="text-xl font-semibold">🤖 AI Market Prediction</h2>
          <p className="text-lg mt-1">{pred}</p>
        </div>
      </div>

      {/* Memoria y rendimiento */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-xl font-semibold">📘 Episodic Summary</h2>
          {summary.length === 0 ? (
            <p className="text-sm text-gray-500 italic">No data yet.</p>
          ) : (
            <ul className="text-sm list-disc ml-4">
              {summary.map((item, idx) => (
                <li key={idx}>
                  Ep {item.episode}: 🏆 Reward {item.reward} / 📉 Loss {item.avg_loss_like_signal}
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card">
          <h2 className="text-xl font-semibold">📊 Memory Stats</h2>
          {stats ? (
            <div className="text-sm space-y-1">
              <p>Total Episodes: {stats.total_episodes}</p>
              <p>Avg. Reward: {stats.average_reward}</p>
              <p>Avg. Loss Signal: {stats.average_loss_signal}</p>
            </div>
          ) : (
            <p className="text-sm text-gray-500 italic">No stats available.</p>
          )}
        </div>
      </div>

      {/* Consola de logs */}
      <div className="card">
        <h2 className="text-xl font-semibold">📜 Training Logs</h2>
        <div className="console-output">
          {logs.length === 0 ? (
            <p className="text-xs text-gray-500 italic">No logs yet.</p>
          ) : (
            logs.map((log, index) => (
              <div key={index} className="text-xs whitespace-pre-wrap">{log}</div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
