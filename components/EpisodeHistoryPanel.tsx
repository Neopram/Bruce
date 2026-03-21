// Ruta: frontend/components/EpisodeHistoryPanel.tsx

import React, { useEffect, useState } from "react"
import axios from "axios"

interface Episode {
  episode: number
  total_steps: number
  reward: number
  avg_loss_like_signal: number
  timestamp: string
}

export default function EpisodeHistoryPanel() {
  const [episodes, setEpisodes] = useState<Episode[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchEpisodes()
  }, [])

  const fetchEpisodes = async () => {
    try {
      const response = await axios.get("http://localhost:8001/api/v1/episodes")
      setEpisodes(response.data.reverse()) // Mostrar más recientes primero
    } catch (error) {
      console.error("Error fetching episodes:", error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 bg-white rounded-xl shadow-md border">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        Episode Training History
      </h2>

      {loading ? (
      ) : episodes.length === 0 ? (
        <p className="text-sm text-gray-500">No episodes found.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm text-left">
            <thead>
              <tr>
                <th className="px-4 py-2">Episode</th>
                <th className="px-4 py-2">Steps</th>
                <th className="px-4 py-2">Reward</th>
                <th className="px-4 py-2">Loss</th>
                <th className="px-4 py-2">Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {episodes.map((ep) => (
                <tr key={ep.timestamp} className="border-t">
                  <td className="px-4 py-2">{ep.episode}</td>
                  <td className="px-4 py-2">{ep.total_steps}</td>
                  <td className="px-4 py-2">{ep.reward.toFixed(2)}</td>
                  <td className="px-4 py-2">{ep.avg_loss_like_signal.toFixed(4)}</td>
                  <td className="px-4 py-2">{new Date(ep.timestamp).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
