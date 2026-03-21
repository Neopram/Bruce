import React, { useState, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface PromptEntry {
  id: string;
  timestamp: string;
  prompt: string;
  tokenCount: number;
  response?: string;
}

function tokenize(text: string): number {
  return Math.ceil(text.split(/\s+/).length * 1.3);
}

function SyntaxHighlight({ text }: { text: string }) {
  const lines = text.split("\n");
  return (
    <pre className="text-sm leading-relaxed overflow-x-auto">
      {lines.map((line, i) => {
        let cls = "text-gray-300";
        if (line.startsWith("###") || line.startsWith("##") || line.startsWith("#")) cls = "text-cyan-400 font-bold";
        else if (line.startsWith("//") || line.startsWith("---")) cls = "text-gray-500";
        else if (line.match(/^\s*\{/)) cls = "text-yellow-300";
        else if (line.match(/^\s*"[^"]+"\s*:/)) cls = "text-purple-300";
        else if (line.startsWith("System:") || line.startsWith("User:") || line.startsWith("Assistant:")) cls = "text-green-400 font-semibold";
        return (
          <div key={i} className="flex">
            <span className="w-8 text-right pr-3 text-gray-600 select-none text-xs">{i + 1}</span>
            <span className={cls}>{line || " "}</span>
          </div>
        );
      })}
    </pre>
  );
}

export default function PromptInspector() {
  const [currentPrompt, setCurrentPrompt] = useState(
    "System: You are Bruce, an AI trading assistant.\n\n### Context\nMarket: BTC/USDT\nTimeframe: 1H\nCurrent Price: $67,432\n\n### Instructions\nAnalyze the current market conditions and provide a trade recommendation.\nConsider risk/reward ratio and current portfolio exposure.\n\nUser: What's your analysis of the current BTC setup?"
  );
  const [history, setHistory] = useState<PromptEntry[]>([]);
  const [running, setRunning] = useState(false);
  const [response, setResponse] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runPrompt = useCallback(async () => {
    setRunning(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/bruce-api/prompt/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: currentPrompt }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const resp = data.response || data.result || "No response received.";
      setResponse(resp);
      const entry: PromptEntry = {
        id: Date.now().toString(),
        timestamp: new Date().toISOString().slice(11, 19),
        prompt: currentPrompt,
        tokenCount: tokenize(currentPrompt),
        response: resp,
      };
      setHistory((prev) => [entry, ...prev].slice(0, 20));
    } catch (err: any) {
      setError(err.message || "Failed to run prompt");
      setResponse(null);
    } finally {
      setRunning(false);
    }
  }, [currentPrompt]);

  const tokens = tokenize(currentPrompt);

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-orange-300">Prompt Inspector</h2>
        <span className="text-xs text-gray-400 font-mono">{tokens} tokens (est.)</span>
      </div>

      {/* Prompt Editor */}
      <div className="bg-gray-950 border border-gray-700 rounded-lg overflow-hidden">
        <div className="flex items-center justify-between px-3 py-1.5 bg-gray-800 border-b border-gray-700">
          <span className="text-xs text-gray-400">Prompt Editor</span>
          <div className="flex gap-2">
            <button
              onClick={runPrompt}
              disabled={running || !currentPrompt.trim()}
              className="text-xs px-3 py-1 bg-orange-700 hover:bg-orange-600 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded"
            >
              {running ? "Running..." : "Run"}
            </button>
          </div>
        </div>
        <textarea
          value={currentPrompt}
          onChange={(e) => setCurrentPrompt(e.target.value)}
          className="w-full h-40 bg-gray-950 text-gray-300 font-mono text-sm p-3 focus:outline-none resize-y"
          spellCheck={false}
        />
      </div>

      {/* Syntax Preview */}
      <div className="bg-gray-950 border border-gray-700 rounded-lg p-3 max-h-48 overflow-y-auto font-mono">
        <span className="text-xs text-gray-500 mb-2 block">Syntax Preview</span>
        <SyntaxHighlight text={currentPrompt} />
      </div>

      {/* Response */}
      {response && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-3">
          <span className="text-xs text-gray-400">Response</span>
          <p className="text-sm text-gray-300 mt-1 whitespace-pre-wrap font-mono">{response}</p>
        </div>
      )}

      {error && <p className="text-red-400 text-xs">{error}</p>}

      {/* History */}
      {history.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-400 mb-2">History</h3>
          <div className="space-y-1 max-h-40 overflow-y-auto">
            {history.map((entry) => (
              <div
                key={entry.id}
                onClick={() => setCurrentPrompt(entry.prompt)}
                className="flex items-center justify-between p-2 bg-gray-800 rounded cursor-pointer hover:bg-gray-750 border border-gray-700"
              >
                <span className="text-xs text-gray-300 truncate flex-1 mr-2">{entry.prompt.slice(0, 60)}...</span>
                <div className="flex items-center gap-2 text-[10px] text-gray-500">
                  <span>{entry.tokenCount} tok</span>
                  <span>{entry.timestamp}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
