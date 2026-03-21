// Ruta: C:\Users\feder\Desktop\OKK_Gorilla_Bot\frontend\components\RLTrainerPanel.tsx

import React, { useState, useEffect } from "react"
import axios from "axios"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001"

export default function RLTrainerPanel() {
  const [status, setStatus] = useState("Idle")
  const [logs, setLogs] = useState<string[]>([])
  const [training, setTraining] = useState(false)
  const [modelName, setModelName] = useState("ppo_gorilla_agent")
  const [learningRate, setLearningRate] = useState(0.00025)
  const [episodes, setEpisodes] = useState(1000)
  const [env, setEnv] = useState("MarketEnv-v1")
  const [summary, setSummary] = useState<any>(null)
  const [stats, setStats] = useState<any>(null)

  const fetchLogs = async () => {
    try {
      const response = await axios.get(`${API_URL}/train/logs`)
      setLogs(response.data.logs || [])
    } catch (err) {
      setLogs(["Unable to retrieve logs."])
    }
  }

  const fetchMemorySummary = async () => {
    try {
      const response = await axios.get(`${API_URL}/memory/summary`)
      setSummary(response.data)
    } catch (err) {
      setSummary(null)
    }
  }

  const fetchStatistics = async () => {
    try {
      const response = await axios.get(`${API_URL}/memory/stats`)
      setStats(response.data)
    } catch (err) {
      setStats(null)
    }
  }

  useEffect(() => {
    if (training) {
      const interval = setInterval(() => {
        fetchLogs()
        fetchMemorySummary()
        fetchStatistics()
      }, 5000)
      return () => clearInterval(interval)
    }
  }, [training])

  const triggerTraining = async () => {
    setTraining(true)
    setLogs([])
    try {
      const response = await axios.post(`${API_URL}/train/start`, {
        model_name: modelName,
        env_name: env,
        learning_rate: learningRate,
        episodes: episodes,
      })
      setStatus("Completed")
      setLogs(response.data.logs || ["Training finished."])
    } catch (err: any) {
      setStatus("Error")
      setLogs(["❌ Training failed. Check backend service or logs."])
    }
    setTraining(false)
    fetchMemorySummary()
    fetchStatistics()
  }

  const stopTraining = async () => {
    try {
      await axios.post(`${API_URL}/train/stop`)
      setStatus("Stopped")
    } catch {
    }
    setTraining(false)
  }

  return (
    <div className="p-6 border rounded-2xl shadow-md bg-white space-y-6">
      <h2 className="text-2xl font-semibold">🤖 RL Trainer Panel</h2>
      <p className="text-gray-600 text-sm">
        Launch and monitor training of your PPO agent. This is where the bot evolves.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium">Model Name</label>
          <input
            className="border p-2 rounded w-full"
            value={modelName}
            onChange={e => setModelName(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium">Learning Rate</label>
          <input
            type="number"
            step="0.00001"
            className="border p-2 rounded w-full"
            value={learningRate}
            onChange={e => setLearningRate(Number(e.target.value))}
          />
        </div>
        <div>
          <label className="block text-sm font-medium">Episodes</label>
          <input
            type="number"
            className="border p-2 rounded w-full"
            value={episodes}
            onChange={e => setEpisodes(Number(e.target.value))}
          />
        </div>
        <div>
          <label className="block text-sm font-medium">Environment</label>
          <input
            className="border p-2 rounded w-full"
            value={env}
            onChange={e => setEnv(e.target.value)}
          />
        </div>
      </div>

      <div className="flex gap-4 pt-4">
        <button
          onClick={triggerTraining}
          disabled={training}
          className="px-4 py-2 bg-blue-700 hover:bg-blue-800 text-white rounded"
        >
          Start Training
        </button>
        <button
          onClick={stopTraining}
          className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded"
        >
          Stop
        </button>
      </div>

      <div className="text-sm text-gray-700 mt-4">
        <strong>Status:</strong> {status}
      </div>

      <div className="max-h-64 overflow-y-auto mt-2 p-2 bg-gray-50 border rounded">
        {logs.length === 0 ? (
          <div className="text-xs text-gray-500 italic">No logs available yet.</div>
        ) : (
          logs.map((line, index) => (
            <div key={index} className="text-xs text-gray-800">{line}</div>
          ))
        )}
      </div>

      {summary && (
        <div className="mt-4 text-sm text-gray-800">
          <h4 className="font-semibold">📘 Episodic Summary</h4>
          <ul className="list-disc ml-4">
            {summary.map((s: any, idx: number) => (
              <li key={idx}>Episode {s.episode} → Reward: {s.reward}, Loss: {s.avg_loss_like_signal}</li>
            ))}
          </ul>
        </div>
      )}

      {stats && (
        <div className="mt-2 text-sm text-gray-800">
          <h4 className="font-semibold">📊 Memory Stats</h4>
          <p>Total Episodes: {stats.total_episodes}</p>
          <p>Avg. Reward: {stats.average_reward}</p>
          <p>Avg. Loss Signal: {stats.average_loss_signal}</p>
        </div>
      )}
    </div>
  )
}
