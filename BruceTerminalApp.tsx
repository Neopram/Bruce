import React, { useState, useEffect, useRef } from 'react'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { Mic, PlayCircle, SendHorizonal } from 'lucide-react'
import toast from 'react-hot-toast'

export default function BruceTerminalApp() {
  const [history, setHistory] = useState<{ role: string, message: string }[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [activeModel, setActiveModel] = useState("phi3")  // Establece Phi3 como el modelo por defecto
  const bottomRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [history])

  const handleSend = async () => {
    if (!input.trim()) return
    setLoading(true)
    const userMessage = { role: "user", message: input }
    setHistory(prev => [...prev, userMessage])

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/terminal/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input, model: activeModel }),  // Asegúrate de incluir el modelo seleccionado
      })
      const data = await res.json()
      setHistory(prev => [...prev, { role: "bruce", message: data.response || "Sin respuesta." }])
    } catch (err) {
      toast.error("Error al conectar con Bruce.")
    } finally {
      setLoading(false)
      setInput("")
    }
  }

  return (
    <div className="flex flex-col h-screen bg-black text-white font-mono">
      <div className="p-4 text-xl border-b border-gray-800 bg-gradient-to-r from-blue-900 to-gray-900">
        Bruce Terminal <span className="text-sm text-gray-400">Symbiotic Console</span>
      </div>

      <div className="flex-1 overflow-y-scroll p-4 space-y-4">
        {history.map((msg, i) => (
          <div key={i} className={`whitespace-pre-wrap text-sm ${msg.role === "bruce" ? "text-green-400" : "text-blue-400"}`}>
            <b>{msg.role === "bruce" ? "🧠 Bruce:" : "🧍 You:"}</b> {msg.message}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="flex items-center gap-2 p-4 border-t border-gray-800 bg-black">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask Bruce anything..."
          className="flex-1 bg-gray-900 text-white border border-gray-700"
          rows={2}
        />
        <Button disabled={loading} onClick={handleSend} className="bg-green-700 hover:bg-green-600">
          <SendHorizonal size={18} />
        </Button>
        <Button variant="outline"><Mic size={18} /></Button>
        <Button variant="outline"><PlayCircle size={18} /></Button>
      </div>
    </div>
  )
}
