import React, { useState, useEffect, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface PromptSection {
  id: string;
  type: "system" | "user" | "context" | "instructions" | "examples";
  label: string;
  content: string;
  tokenCount: number;
}

const SECTION_COLORS: Record<string, { bg: string; border: string; text: string; bar: string }> = {
  system: { bg: "bg-red-900/20", border: "border-red-700", text: "text-red-300", bar: "bg-red-500" },
  user: { bg: "bg-blue-900/20", border: "border-blue-700", text: "text-blue-300", bar: "bg-blue-500" },
  context: { bg: "bg-green-900/20", border: "border-green-700", text: "text-green-300", bar: "bg-green-500" },
  instructions: { bg: "bg-yellow-900/20", border: "border-yellow-700", text: "text-yellow-300", bar: "bg-yellow-500" },
  examples: { bg: "bg-purple-900/20", border: "border-purple-700", text: "text-purple-300", bar: "bg-purple-500" },
};

function estimateTokens(text: string): number {
  return Math.ceil(text.split(/\s+/).length * 1.3);
}

export default function PromptVisualizer() {
  const [sections, setSections] = useState<PromptSection[]>([]);
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPrompt = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/bruce-api/prompt/current`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setSections(
        (data.sections || []).map((s: any, i: number) => ({
          id: s.id || `section-${i}`,
          type: s.type || "context",
          label: s.label || s.type || "Section",
          content: s.content || "",
          tokenCount: s.token_count ?? estimateTokens(s.content || ""),
        }))
      );
      setError(null);
    } catch {
      setSections([
        { id: "s1", type: "system", label: "System Prompt", content: "You are Bruce, an advanced AI trading assistant built for cryptocurrency markets. You have deep knowledge of technical analysis, on-chain metrics, and market microstructure.", tokenCount: 42 },
        { id: "s2", type: "context", label: "Market Context", content: "Current Market State:\n- BTC/USDT: $67,432 (+2.1%)\n- ETH/USDT: $3,891 (+1.5%)\n- Market Cap: $2.4T\n- Fear & Greed: 72 (Greed)\n- 24h Volume: $89.2B", tokenCount: 68 },
        { id: "s3", type: "instructions", label: "Task Instructions", content: "Analyze the current market and provide:\n1. Short-term (4H) directional bias\n2. Key support/resistance levels\n3. Risk assessment (1-10)\n4. Recommended position size (%)\n5. Stop-loss and take-profit levels", tokenCount: 55 },
        { id: "s4", type: "examples", label: "Few-Shot Examples", content: "Example Output:\n{\n  \"bias\": \"bullish\",\n  \"confidence\": 0.78,\n  \"support\": [66800, 65200],\n  \"resistance\": [68500, 70000],\n  \"risk\": 6,\n  \"position_pct\": 5\n}", tokenCount: 48 },
        { id: "s5", type: "user", label: "User Query", content: "What's the best entry point for a BTC long right now? My portfolio is 40% allocated.", tokenCount: 22 },
      ]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchPrompt(); }, [fetchPrompt]);

  const toggleCollapse = (id: string) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const totalTokens = sections.reduce((sum, s) => sum + s.tokenCount, 0);

  if (loading) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 animate-pulse space-y-3">
        <div className="h-4 bg-gray-700 rounded w-1/3" />
        {[1, 2, 3].map((i) => <div key={i} className="h-20 bg-gray-800 rounded" />)}
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-teal-300">Prompt Visualizer</h2>
        <span className="text-xs text-gray-400 font-mono">{totalTokens} total tokens</span>
      </div>

      {/* Token Distribution Bar */}
      <div className="w-full h-4 bg-gray-800 rounded-full overflow-hidden flex">
        {sections.map((section) => {
          const pct = totalTokens > 0 ? (section.tokenCount / totalTokens) * 100 : 0;
          const colors = SECTION_COLORS[section.type] || SECTION_COLORS.context;
          return (
            <div
              key={section.id}
              className={`${colors.bar} h-full transition-all relative group`}
              style={{ width: `${pct}%` }}
              title={`${section.label}: ${section.tokenCount} tokens (${pct.toFixed(1)}%)`}
            />
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3">
        {sections.map((section) => {
          const colors = SECTION_COLORS[section.type] || SECTION_COLORS.context;
          return (
            <div key={section.id} className="flex items-center gap-1.5 text-xs">
              <span className={`w-2.5 h-2.5 rounded-sm ${colors.bar}`} />
              <span className="text-gray-400">{section.label}</span>
              <span className="text-gray-500 font-mono">({section.tokenCount})</span>
            </div>
          );
        })}
      </div>

      {/* Sections */}
      <div className="space-y-2">
        {sections.map((section) => {
          const colors = SECTION_COLORS[section.type] || SECTION_COLORS.context;
          const isCollapsed = collapsed.has(section.id);
          return (
            <div key={section.id} className={`rounded-lg border ${colors.border} ${colors.bg} overflow-hidden`}>
              <div
                className="flex items-center justify-between px-3 py-2 cursor-pointer hover:bg-gray-800/30"
                onClick={() => toggleCollapse(section.id)}
              >
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">{isCollapsed ? "+" : "-"}</span>
                  <span className={`text-xs font-semibold ${colors.text}`}>{section.label}</span>
                  <span className="text-[10px] text-gray-500 uppercase">{section.type}</span>
                </div>
                <span className="text-[10px] text-gray-500 font-mono">{section.tokenCount} tokens</span>
              </div>
              {!isCollapsed && (
                <div className="px-3 pb-3 border-t border-gray-800">
                  <pre className="text-sm text-gray-300 font-mono whitespace-pre-wrap leading-relaxed mt-2">{section.content}</pre>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {error && <p className="text-red-400 text-xs">{error}</p>}
      <button onClick={fetchPrompt} className="px-3 py-1.5 bg-teal-800 hover:bg-teal-700 text-teal-200 text-xs rounded">Refresh</button>
    </div>
  );
}
