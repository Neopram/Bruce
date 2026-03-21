import React, { useState } from "react"
import axios from "axios"
import { toast } from "react-toastify"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001"

export default function DeepSeekSupervisorPanel() {
  const [prompt, setPrompt] = useState("")
  const [command, setCommand] = useState("")
  const [response, setResponse] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    const finalCommand = prompt || command

    if (!finalCommand.trim()) {
      toast.warning("Please enter a command or instruction.")
      return
    }

    setLoading(true)
    setResponse(null)

    try {
      const res = await axios.post(`${API_URL}/ai/deepseek/control`, {
        command: finalCommand,
        context: {}, // Puedes enviar más información del entorno aquí si lo deseas
      })

      const reply = res.data.response || "No response received from DeepSeek."
      setResponse(reply)
    } catch (err) {
      console.error("DeepSeek Supervisor Error:", err)
      toast.error("Failed to reach DeepSeek control API.")
    }

    setLoading(false)
  }

  return (
    <div className="p-6 bg-white rounded-2xl shadow border space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">🧠 DeepSeek Supervisor Panel</h2>

      <p className="text-sm text-gray-600">
        Send high-level cognitive commands to the DeepSeek Core Controller.
        This interface allows you to retrain models, activate governance, trigger autopsies,
        or reconfigure the architecture dynamically using natural language.
      </p>

      <textarea
        value={prompt}
        onChange={(e) => {
          setPrompt(e.target.value)
          setCommand(e.target.value) // sincronicemos ambos
        }}
        placeholder="Ex: Retrain model with custom reward function and activate DAO proposal #17."
        className="w-full p-3 border rounded text-sm"
        rows={4}
      />

      <div className="flex justify-end">
        <button
          onClick={handleSubmit}
          disabled={loading}
          className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded"
        >
        </button>
      </div>

      {response && (
        <div className="mt-4 bg-gray-100 p-4 border rounded text-sm text-gray-800 whitespace-pre-wrap">
          <h3 className="font-semibold mb-2">DeepSeek Response:</h3>
          <div>{response}</div>
        </div>
      )}
    </div>
  )
}
