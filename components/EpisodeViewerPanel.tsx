// Ruta: C:\Users\feder\Desktop\OKK_Gorilla_Bot\frontend\components\EpisodeViewerPanel.tsx

import React, { useEffect, useState } from "react"
import axios from "axios"
import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts"
import { Line as ChartJSLine } from "react-chartjs-2"
import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip as ChartTooltip,
  Legend as ChartLegend
} from "chart.js"
import { toast } from "react-toastify"

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, ChartTooltip, ChartLegend)

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001"

export default function EpisodeViewerPanel() {
  const [episodes, setEpisodes] = useState<any[]>([])
  const [stats, setStats] = useState<any | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchSummary = async () => {
    try {
      const res = await axios.get(`${API_URL}/memory/summary`)
      setEpisodes(res.data || [])
    } catch (err) {
      toast.error("Error fetching episode summary")
    }
  }

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API_URL}/memory/stats`)
      setStats(res.data || null)
    } catch (err) {
      toast.error("Error fetching stats")
    }
  }

  useEffect(() => {
    fetchSummary()
    fetchStats()
    const interval = setInterval(() => {
      fetchSummary()
      fetchStats()
    }, 10000)
    return () => clearInterval(interval)
  }, [])

  const chartData = {
    labels: episodes.map((ep, idx) => `Ep ${ep.episode || idx}`),
    datasets: [
      {
        label: "Reward",
        data: episodes.map(ep => ep.reward),
        borderColor: "#10b981",
        backgroundColor: "rgba(16,185,129,0.2)",
        tension: 0.3,
      },
      {
        label: "Loss Signal",
        data: episodes.map(ep => ep.avg_loss_like_signal),
        borderColor: "#ef4444",
        backgroundColor: "rgba(239,68,68,0.2)",
        tension: 0.3,
      },
    ],
  }

  return (
    <div className="p-6 bg-white rounded-2xl shadow border space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">📊 Episode Performance Overview</h2>

      {stats && (
        <div className="grid grid-cols-2 gap-6 text-sm text-gray-700">
          <div><strong>Total Episodes:</strong> {stats.total_episodes}</div>
          <div><strong>Avg. Reward:</strong> {stats.average_reward}</div>
          <div><strong>Avg. Loss Signal:</strong> {stats.average_loss_signal}</div>
        </div>
      )}

      {/* CHART.JS - Reinforcement Summary */}
      <div className="bg-gray-50 p-4 border rounded">
        <ChartJSLine data={chartData} height={100} />
      </div>

      {/* Recharts - Trend Comparison */}
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={episodes} margin={{ top: 10, right: 30, bottom: 10, left: 0 }}>
            <Line type="monotone" dataKey="reward" stroke="#2563eb" strokeWidth={2} name="Reward" />
            <Line type="monotone" dataKey="avg_loss_like_signal" stroke="#dc2626" strokeWidth={2} name="Loss Signal" />
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="episode" />
            <YAxis />
            <Tooltip />
            <Legend />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}