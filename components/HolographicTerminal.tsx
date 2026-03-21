import React, { useState, useRef, useEffect } from "react";

interface TerminalLine {
  id: string;
  type: "input" | "output" | "error" | "system";
  content: string;
}

export default function HolographicTerminal() {
  const [lines, setLines] = useState<TerminalLine[]>([
    { id: "0", type: "system", content: "BRUCE AI HOLOGRAPHIC TERMINAL v2.0" },
    { id: "1", type: "system", content: "Quantum encryption: ACTIVE | Neural link: STABLE" },
    { id: "2", type: "system", content: "Type 'help' for available commands." },
  ]);
  const [input, setInput] = useState("");
  const [history, setHistory] = useState<string[]>([]);
  const [historyIdx, setHistoryIdx] = useState(-1);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [lines]);

  const processCommand = (cmd: string) => {
    const addLine = (type: TerminalLine["type"], content: string) =>
      ({ id: Date.now().toString() + Math.random(), type, content });

    const newLines: TerminalLine[] = [addLine("input", `> ${cmd}`)];

    const c = cmd.trim().toLowerCase();
    if (c === "help") {
      newLines.push(addLine("output", "Available commands:"));
      newLines.push(addLine("output", "  status    - System status overview"));
      newLines.push(addLine("output", "  scan      - Scan market conditions"));
      newLines.push(addLine("output", "  emotion   - Current emotional state"));
      newLines.push(addLine("output", "  models    - List loaded AI models"));
      newLines.push(addLine("output", "  clear     - Clear terminal"));
      newLines.push(addLine("output", "  help      - Show this help"));
    } else if (c === "status") {
      newLines.push(addLine("output", "SYSTEM STATUS: OPERATIONAL"));
      newLines.push(addLine("output", "  CPU: 42% | RAM: 5.2/16 GB | GPU: 67%"));
      newLines.push(addLine("output", "  Uptime: 3d 14h 27m | Sessions: 3"));
      newLines.push(addLine("output", "  Neural Engine: ACTIVE | Latency: 23ms"));
    } else if (c === "scan") {
      newLines.push(addLine("output", "SCANNING MARKET CONDITIONS..."));
      newLines.push(addLine("output", "  BTC/USDT: $67,432 (+2.1%) | Vol: HIGH"));
      newLines.push(addLine("output", "  Trend: BULLISH | RSI: 68 | MACD: +"));
      newLines.push(addLine("output", "  Fear & Greed: 72 (GREED)"));
      newLines.push(addLine("output", "  Recommendation: CAUTIOUS LONG"));
    } else if (c === "emotion") {
      newLines.push(addLine("output", "EMOTIONAL STATE REPORT:"));
      newLines.push(addLine("output", "  Dominant: FOCUSED (0.82)"));
      newLines.push(addLine("output", "  Joy: 0.45 | Trust: 0.71 | Fear: 0.12"));
      newLines.push(addLine("output", "  Trading suitability: HIGH"));
    } else if (c === "models") {
      newLines.push(addLine("output", "LOADED MODELS:"));
      newLines.push(addLine("output", "  [ACTIVE] deepseek-v3   | 45.2 tok/s | 234ms"));
      newLines.push(addLine("output", "  [IDLE]   gpt-4o        | --        | --"));
      newLines.push(addLine("output", "  [ACTIVE] emotion-v2    | 120 tok/s | 8ms"));
    } else if (c === "clear") {
      setLines([]);
      return;
    } else if (c === "") {
      return;
    } else {
      newLines.push(addLine("error", `Unknown command: '${cmd}'. Type 'help' for available commands.`));
    }

    setLines((prev) => [...prev, ...newLines]);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    processCommand(input);
    setHistory((prev) => [input, ...prev]);
    setHistoryIdx(-1);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowUp") {
      e.preventDefault();
      const next = Math.min(historyIdx + 1, history.length - 1);
      setHistoryIdx(next);
      setInput(history[next] || "");
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      const next = Math.max(historyIdx - 1, -1);
      setHistoryIdx(next);
      setInput(next >= 0 ? history[next] : "");
    }
  };

  const LINE_COLORS: Record<string, string> = {
    input: "text-cyan-300",
    output: "text-green-300",
    error: "text-red-400",
    system: "text-purple-400",
  };

  return (
    <div className="bg-black border border-cyan-900/50 rounded-xl overflow-hidden relative">
      {/* Scanline overlay */}
      <div className="absolute inset-0 pointer-events-none z-10 opacity-[0.03]"
        style={{ background: "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,255,255,0.1) 2px, rgba(0,255,255,0.1) 4px)" }}
      />
      {/* Glow border */}
      <div className="absolute inset-0 pointer-events-none rounded-xl" style={{ boxShadow: "inset 0 0 30px rgba(0,255,255,0.05), 0 0 20px rgba(0,255,255,0.1)" }} />

      <div className="relative z-20 p-4 space-y-2">
        <div className="flex items-center justify-between border-b border-cyan-900/30 pb-2">
          <h2 className="text-sm font-bold text-cyan-400 font-mono tracking-wider" style={{ textShadow: "0 0 10px rgba(0,255,255,0.5)" }}>
            HOLOGRAPHIC TERMINAL
          </h2>
          <div className="flex gap-1.5">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="w-2 h-2 rounded-full bg-cyan-500" />
            <span className="w-2 h-2 rounded-full bg-purple-500" />
          </div>
        </div>

        <div ref={scrollRef} className="h-64 overflow-y-auto space-y-0.5 font-mono text-xs" style={{ textShadow: "0 0 5px rgba(0,255,255,0.3)" }}>
          {lines.map((line) => (
            <div key={line.id} className={`${LINE_COLORS[line.type]} leading-relaxed`}>
              {line.content}
            </div>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="flex items-center gap-2 border-t border-cyan-900/30 pt-2">
          <span className="text-cyan-500 font-mono text-sm" style={{ textShadow: "0 0 8px rgba(0,255,255,0.6)" }}>$</span>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1 bg-transparent text-cyan-300 font-mono text-sm focus:outline-none placeholder:text-cyan-900"
            placeholder="Enter command..."
            autoFocus
            style={{ textShadow: "0 0 5px rgba(0,255,255,0.3)" }}
          />
        </form>
      </div>
    </div>
  );
}
