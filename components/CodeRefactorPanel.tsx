import React, { useState } from "react";

interface Suggestion {
  id: string;
  title: string;
  description: string;
  severity: "info" | "warning" | "critical";
  file: string;
  line: number;
  before: string;
  after: string;
  applied: boolean;
}

const SEVERITY_STYLES: Record<string, { badge: string; text: string }> = {
  info: { badge: "bg-blue-900 text-blue-300", text: "text-blue-300" },
  warning: { badge: "bg-yellow-900 text-yellow-300", text: "text-yellow-300" },
  critical: { badge: "bg-red-900 text-red-300", text: "text-red-300" },
};

export default function CodeRefactorPanel() {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([
    {
      id: "s1", title: "Replace var with const", description: "Variables not reassigned should use const for immutability.",
      severity: "info", file: "utils/helpers.ts", line: 12,
      before: "var apiUrl = process.env.API_URL;",
      after: "const apiUrl = process.env.API_URL;",
      applied: false,
    },
    {
      id: "s2", title: "Extract duplicate logic", description: "Repeated fetch pattern found in 3 components. Extract to shared hook.",
      severity: "warning", file: "components/Dashboard.tsx", line: 45,
      before: "const res = await fetch(url);\nif (!res.ok) throw new Error();\nconst data = await res.json();",
      after: "const data = await useFetch<T>(url);",
      applied: false,
    },
    {
      id: "s3", title: "Remove unused import", description: "axios imported but never used. Using native fetch instead.",
      severity: "info", file: "components/AIHealthMonitor.tsx", line: 3,
      before: 'import axios from "axios";',
      after: "// removed unused import",
      applied: false,
    },
    {
      id: "s4", title: "Fix potential null reference", description: "Accessing property on potentially undefined object without null check.",
      severity: "critical", file: "hooks/useEmotion.ts", line: 28,
      before: "return data.emotion.dominant;",
      after: "return data?.emotion?.dominant ?? 'neutral';",
      applied: false,
    },
  ]);
  const [selected, setSelected] = useState<string | null>(null);

  const applySuggestion = (id: string) => {
    setSuggestions((prev) => prev.map((s) => s.id === id ? { ...s, applied: true } : s));
  };

  const rejectSuggestion = (id: string) => {
    setSuggestions((prev) => prev.filter((s) => s.id !== id));
  };

  const applyAll = () => {
    setSuggestions((prev) => prev.map((s) => ({ ...s, applied: true })));
  };

  const pending = suggestions.filter((s) => !s.applied);
  const applied = suggestions.filter((s) => s.applied);

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-cyan-300">Code Refactor</h2>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">{pending.length} pending</span>
          {pending.length > 0 && (
            <button onClick={applyAll} className="text-[10px] px-2 py-1 bg-cyan-800 text-cyan-200 rounded hover:bg-cyan-700">
              Apply All
            </button>
          )}
        </div>
      </div>

      {/* Suggestion List */}
      <div className="space-y-2">
        {suggestions.map((s) => {
          const style = SEVERITY_STYLES[s.severity];
          const isSelected = selected === s.id;
          return (
            <div key={s.id} className={`border rounded-lg overflow-hidden transition-colors ${s.applied ? "border-green-800 bg-green-900/10 opacity-60" : "border-gray-700 bg-gray-800"}`}>
              <div
                className="p-3 cursor-pointer hover:bg-gray-750"
                onClick={() => setSelected(isSelected ? null : s.id)}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className={`text-[9px] px-1.5 py-0.5 rounded ${style.badge}`}>{s.severity}</span>
                    <span className="text-sm text-gray-200">{s.title}</span>
                    {s.applied && <span className="text-[9px] text-green-400">APPLIED</span>}
                  </div>
                  <span className="text-[10px] text-gray-500">{s.file}:{s.line}</span>
                </div>
                <p className="text-xs text-gray-400">{s.description}</p>
              </div>

              {isSelected && (
                <div className="border-t border-gray-700 p-3 space-y-2">
                  {/* Diff View */}
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <span className="text-[10px] text-red-400 mb-1 block">Before</span>
                      <pre className="text-xs bg-red-950/30 border border-red-900/30 rounded p-2 text-red-300 font-mono whitespace-pre-wrap">{s.before}</pre>
                    </div>
                    <div>
                      <span className="text-[10px] text-green-400 mb-1 block">After</span>
                      <pre className="text-xs bg-green-950/30 border border-green-900/30 rounded p-2 text-green-300 font-mono whitespace-pre-wrap">{s.after}</pre>
                    </div>
                  </div>

                  {!s.applied && (
                    <div className="flex gap-2 pt-1">
                      <button onClick={() => applySuggestion(s.id)} className="text-xs px-3 py-1 bg-green-700 hover:bg-green-600 text-white rounded">
                        Apply
                      </button>
                      <button onClick={() => rejectSuggestion(s.id)} className="text-xs px-3 py-1 bg-red-800 hover:bg-red-700 text-red-200 rounded">
                        Reject
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {suggestions.length === 0 && (
        <p className="text-gray-600 text-sm text-center py-6">No refactoring suggestions available</p>
      )}
    </div>
  );
}
