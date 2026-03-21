
import React, { useState, useEffect, useCallback } from "react"
import { Card, CardContent } from "@/components/ui/card"
import Badge from "@/components/ui/badge"
import Progress from "@/components/ui/progress"

interface AvatarForm {
  id: string
  name: string
  description: string
  energy: number
  mood: string
  active: boolean
}

const AVATAR_FORMS: AvatarForm[] = [
  { id: "bull", name: "Wall Street Bull 2.0", description: "Aggressive market domination mode", energy: 92, mood: "Confident", active: false },
  { id: "sheikh", name: "Oil Sheikh Holograph", description: "Commodities and energy focused persona", energy: 78, mood: "Strategic", active: false },
  { id: "digital", name: "Digital Cognition Entity", description: "Pure analytical computation mode", energy: 100, mood: "Analytical", active: true },
  { id: "shadow", name: "Shadow Operative", description: "Stealth trading and dark pool access", energy: 65, mood: "Alert", active: false },
  { id: "oracle", name: "Market Oracle", description: "Predictive analysis and trend forecasting", energy: 88, mood: "Focused", active: false },
]

const AvatarVisualConsole = () => {
  const [forms, setForms] = useState<AvatarForm[]>(AVATAR_FORMS)
  const [activeForm, setActiveForm] = useState<AvatarForm>(AVATAR_FORMS.find(f => f.active) || AVATAR_FORMS[0])
  const [transitioning, setTransitioning] = useState(false)
  const [stats, setStats] = useState({
    totalTransformations: 47,
    uptime: 99.7,
    memorySync: 94,
  })

  const switchForm = useCallback((form: AvatarForm) => {
    if (form.id === activeForm.id || transitioning) return
    setTransitioning(true)
    setForms(prev => prev.map(f => ({ ...f, active: f.id === form.id })))
    setTimeout(() => {
      setActiveForm(form)
      setTransitioning(false)
      setStats(prev => ({ ...prev, totalTransformations: prev.totalTransformations + 1 }))
    }, 800)
  }, [activeForm.id, transitioning])

  const moodColor: Record<string, string> = {
    Confident: "text-emerald-400",
    Strategic: "text-indigo-400",
    Analytical: "text-blue-400",
    Alert: "text-amber-400",
    Focused: "text-purple-400",
  }

  return (
    <Card className="bg-gradient-to-br from-gray-900 to-black border-zinc-700">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-white">Bruce Avatar Visual Console</h2>
            <p className="text-sm text-zinc-400 mt-1">Multi-form manifestation controller</p>
          </div>
          <Badge variant={transitioning ? "warning" : "success"} dot>
            {transitioning ? "Morphing..." : "Active"}
          </Badge>
        </div>

        {/* Active Avatar Display */}
        <div className={`mb-6 p-6 rounded-xl bg-gradient-to-r from-zinc-800/80 to-zinc-900/80 border border-zinc-700/50 transition-all duration-500 ${transitioning ? "opacity-50 scale-95" : "opacity-100 scale-100"}`}>
          <div className="flex items-center gap-6">
            <img
              className="w-24 h-24 rounded-xl shadow-lg border border-white/10 object-cover"
              src={`https://robohash.org/${activeForm.name}?set=set2&size=200x200`}
              alt={activeForm.name}
            />
            <div className="flex-1">
              <h3 className="text-xl font-bold text-white">{activeForm.name}</h3>
              <p className="text-sm text-zinc-400 mt-1">{activeForm.description}</p>
              <div className="flex items-center gap-4 mt-3">
                <div>
                  <span className="text-xs text-zinc-500">Mood: </span>
                  <span className={`text-sm font-medium ${moodColor[activeForm.mood] || "text-zinc-300"}`}>
                    {activeForm.mood}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-zinc-500">Energy:</span>
                  <Progress value={activeForm.energy} variant="success" size="sm" className="w-20" />
                  <span className="text-xs font-mono text-zinc-400">{activeForm.energy}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Form Selector */}
        <h3 className="text-sm font-medium text-zinc-400 mb-2">Available Forms</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-4">
          {forms.map((form) => (
            <button
              key={form.id}
              onClick={() => switchForm(form)}
              disabled={transitioning}
              className={`p-3 rounded-lg text-left transition-all ${
                form.id === activeForm.id
                  ? "bg-indigo-900/30 border border-indigo-600/50 ring-1 ring-indigo-500/30"
                  : "bg-zinc-800/50 border border-zinc-700/50 hover:border-zinc-600/50 hover:bg-zinc-800/80"
              } disabled:opacity-50`}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-zinc-200">{form.name}</span>
                {form.id === activeForm.id && <Badge variant="success" size="sm">Active</Badge>}
              </div>
              <p className="text-xs text-zinc-500 mt-0.5">{form.description}</p>
              <Progress value={form.energy} variant={form.energy > 80 ? "success" : "warning"} size="sm" className="mt-2" />
            </button>
          ))}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
            <p className="text-xs text-zinc-500">Transformations</p>
            <p className="text-lg font-bold text-indigo-400">{stats.totalTransformations}</p>
          </div>
          <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
            <p className="text-xs text-zinc-500">Uptime</p>
            <p className="text-lg font-bold text-emerald-400">{stats.uptime}%</p>
          </div>
          <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
            <p className="text-xs text-zinc-500">Memory Sync</p>
            <p className="text-lg font-bold text-blue-400">{stats.memorySync}%</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default AvatarVisualConsole
