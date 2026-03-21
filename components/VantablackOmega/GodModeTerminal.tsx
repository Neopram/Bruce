
import React, { useState, useRef, useCallback, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import Badge from "@/components/ui/badge"
import Progress from "@/components/ui/progress"

interface TerminalLine {
  id: string
  type: "input" | "output" | "error" | "system" | "info"
  content: string
  timestamp: string
}

interface SystemProjection {
  dimensions: string
  timeFolding: boolean
  darkPoolOverlay: boolean
  quantumCoherence: number
  neuralSync: number
  predictiveAccuracy: number
}

const COMMANDS: Record<string, string> = {
  help: "Available: status, scan, predict, heal, override, agents, clear",
  status: "All systems nominal. 7D projection active. Neural sync: 94.2%",
  scan: "Scanning multiversal markets... 47 exchanges, 2,341 pairs monitored.",
  predict: "Predictive engine: BTC likely to test $70k resistance within 48h (confidence: 78%)",
  heal: "Self-healing protocol initiated. 3 micro-anomalies resolved.",
  agents: "Active agents: 12 | Idle: 5 | Total throughput: 847 ops/s",
  override: "GOD MODE: Full override access granted. Use with caution.",
}

const GodModeTerminal = () => {
  const [lines, setLines] = useState<TerminalLine[]>([
    { id: "sys-0", type: "system", content: "=== GOD MODE TERMINAL v2.1 ===", timestamp: new Date().toISOString() },
    { id: "sys-1", type: "system", content: "7D Omniversal projection initialized.", timestamp: new Date().toISOString() },
    { id: "sys-2", type: "info", content: 'Type "help" for available commands.', timestamp: new Date().toISOString() },
  ])
  const [input, setInput] = useState("")
  const [projection, setProjection] = useState<SystemProjection>({
    dimensions: "7D",
    timeFolding: true,
    darkPoolOverlay: true,
    quantumCoherence: 94,
    neuralSync: 91,
    predictiveAccuracy: 78,
  })
  const [commandHistory, setCommandHistory] = useState<string[]>([])
  const [historyIndex, setHistoryIndex] = useState(-1)
  const terminalRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const addLine = useCallback((type: TerminalLine["type"], content: string) => {
    setLines(prev => [...prev, {
      id: `line-${Date.now()}-${Math.random()}`,
      type,
      content,
      timestamp: new Date().toISOString(),
    }])
  }, [])

  const executeCommand = useCallback(async (cmd: string) => {
    const trimmed = cmd.trim().toLowerCase()
    if (!trimmed) return

    addLine("input", `> ${cmd}`)
    setCommandHistory(prev => [...prev, cmd])
    setHistoryIndex(-1)

    if (trimmed === "clear") {
      setLines([])
      return
    }

    if (COMMANDS[trimmed]) {
      addLine("output", COMMANDS[trimmed])
      return
    }

    // Try API
    try {
      addLine("info", "Processing...")
      const res = await fetch("/api/god-mode/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: trimmed }),
      })
      if (res.ok) {
        const data = await res.json()
        addLine("output", data.result || data.message || JSON.stringify(data))
      } else {
        addLine("error", `Command failed (${res.status})`)
      }
    } catch {
      addLine("error", `Unknown command: "${trimmed}". Type "help" for available commands.`)
    }
  }, [addLine])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      executeCommand(input)
      setInput("")
    } else if (e.key === "ArrowUp") {
      e.preventDefault()
      if (commandHistory.length > 0) {
        const newIdx = historyIndex < commandHistory.length - 1 ? historyIndex + 1 : historyIndex
        setHistoryIndex(newIdx)
        setInput(commandHistory[commandHistory.length - 1 - newIdx])
      }
    } else if (e.key === "ArrowDown") {
      e.preventDefault()
      if (historyIndex > 0) {
        const newIdx = historyIndex - 1
        setHistoryIndex(newIdx)
        setInput(commandHistory[commandHistory.length - 1 - newIdx])
      } else {
        setHistoryIndex(-1)
        setInput("")
      }
    }
  }

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [lines])

  const lineColor: Record<TerminalLine["type"], string> = {
    input: "text-cyan-400",
    output: "text-green-400",
    error: "text-red-400",
    system: "text-yellow-400",
    info: "text-zinc-500",
  }

  return (
    <Card className="bg-black border-zinc-700">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-white">God Mode Terminal</h2>
            <p className="text-sm text-zinc-500 mt-0.5">Omniversal command interface</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="error" dot>GOD MODE</Badge>
            <Badge variant="info" size="sm">{projection.dimensions}</Badge>
          </div>
        </div>

        {/* System Status Bar */}
        <div className="grid grid-cols-4 gap-3 mb-4">
          <div className="bg-zinc-900/50 rounded-lg p-2">
            <p className="text-xs text-zinc-500">Quantum Coherence</p>
            <Progress value={projection.quantumCoherence} variant="info" size="sm" />
            <p className="text-xs font-mono text-zinc-400 text-right mt-0.5">{projection.quantumCoherence}%</p>
          </div>
          <div className="bg-zinc-900/50 rounded-lg p-2">
            <p className="text-xs text-zinc-500">Neural Sync</p>
            <Progress value={projection.neuralSync} variant="success" size="sm" />
            <p className="text-xs font-mono text-zinc-400 text-right mt-0.5">{projection.neuralSync}%</p>
          </div>
          <div className="bg-zinc-900/50 rounded-lg p-2">
            <p className="text-xs text-zinc-500">Predictive Accuracy</p>
            <Progress value={projection.predictiveAccuracy} variant="warning" size="sm" />
            <p className="text-xs font-mono text-zinc-400 text-right mt-0.5">{projection.predictiveAccuracy}%</p>
          </div>
          <div className="bg-zinc-900/50 rounded-lg p-2 flex flex-col justify-center items-center gap-1">
            <div className="flex gap-2 text-xs">
              <span className={projection.timeFolding ? "text-emerald-400" : "text-zinc-600"}>TimeFold</span>
              <span className={projection.darkPoolOverlay ? "text-emerald-400" : "text-zinc-600"}>DarkPool</span>
            </div>
          </div>
        </div>

        {/* Terminal */}
        <div
          ref={terminalRef}
          onClick={() => inputRef.current?.focus()}
          className="bg-zinc-950 rounded-lg border border-zinc-800 p-4 font-mono text-sm max-h-[320px] overflow-y-auto cursor-text"
        >
          {lines.map((line) => (
            <div key={line.id} className={`${lineColor[line.type]} leading-relaxed`}>
              {line.content}
            </div>
          ))}
          <div className="flex items-center mt-1">
            <span className="text-cyan-400 mr-2">{">"}</span>
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              className="flex-1 bg-transparent text-cyan-400 outline-none caret-cyan-400"
              autoFocus
              spellCheck={false}
            />
          </div>
        </div>

        <div className="flex items-center justify-between mt-3 text-xs text-zinc-600">
          <span>{lines.length} lines | {commandHistory.length} commands</span>
          <span>Projection: {projection.dimensions} | Folding: {projection.timeFolding ? "Active" : "Off"}</span>
        </div>
      </CardContent>
    </Card>
  )
}

export default GodModeTerminal
