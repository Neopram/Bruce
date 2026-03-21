import React, { useState, useEffect, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface Persona {
  id: string;
  name: string;
  icon: string;
  description: string;
  active: boolean;
}

interface PersonaParams {
  risk: number;
  creativity: number;
  formality: number;
  aggression: number;
}

const DEFAULT_PERSONAS: Persona[] = [
  { id: "analyst", name: "Analyst", icon: "chart", description: "Data-driven decisions with statistical backing.", active: false },
  { id: "strategist", name: "Strategist", icon: "target", description: "Long-term planning with macro perspective.", active: true },
  { id: "degen", name: "Degen", icon: "rocket", description: "High-risk, high-reward momentum plays.", active: false },
  { id: "guardian", name: "Guardian", icon: "shield", description: "Capital preservation and risk management first.", active: false },
  { id: "scout", name: "Scout", icon: "eye", description: "Early detection of emerging trends and narratives.", active: false },
  { id: "mentor", name: "Mentor", icon: "book", description: "Educational approach explaining every decision.", active: false },
];

const ICON_MAP: Record<string, string> = {
  chart: "M-", target: "()", rocket: "/\\", shield: "[]", eye: "@@", book: "{}",
};

function Slider({ label, value, onChange, min = 0, max = 100 }: { label: string; value: number; onChange: (v: number) => void; min?: number; max?: number }) {
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-400">{label}</span>
        <span className="text-gray-300 font-mono">{value}</span>
      </div>
      <input
        type="range" min={min} max={max} value={value} onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-1.5 bg-gray-700 rounded appearance-none cursor-pointer accent-indigo-500"
      />
    </div>
  );
}

export default function PersonaPanel() {
  const [personas, setPersonas] = useState<Persona[]>(DEFAULT_PERSONAS);
  const [params, setParams] = useState<PersonaParams>({ risk: 50, creativity: 60, formality: 70, aggression: 30 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectPersona = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/routers/profile/personality/${id}`, { method: "PUT" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
    } catch { /* proceed locally */ }
    setPersonas((prev) => prev.map((p) => ({ ...p, active: p.id === id })));
    setLoading(false);
  }, []);

  const active = personas.find((p) => p.active);

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-indigo-300">Persona Panel</h2>
        {active && <span className="text-xs text-indigo-400">Active: {active.name}</span>}
      </div>

      {/* Persona Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {personas.map((persona) => (
          <button
            key={persona.id}
            onClick={() => selectPersona(persona.id)}
            disabled={loading}
            className={`p-3 rounded-lg border text-left transition-all ${
              persona.active
                ? "border-indigo-500 bg-indigo-900/30 ring-1 ring-indigo-500/30"
                : "border-gray-700 bg-gray-800 hover:bg-gray-750 hover:border-gray-600"
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-lg font-mono text-indigo-400">{ICON_MAP[persona.icon] || "??"}</span>
              <span className="text-sm font-medium text-gray-200">{persona.name}</span>
            </div>
            <p className="text-[10px] text-gray-400 leading-tight">{persona.description}</p>
          </button>
        ))}
      </div>

      {/* Parameter Sliders */}
      <div className="space-y-3 pt-2">
        <h3 className="text-sm font-semibold text-gray-400">Parameters</h3>
        <Slider label="Risk Tolerance" value={params.risk} onChange={(v) => setParams({ ...params, risk: v })} />
        <Slider label="Creativity" value={params.creativity} onChange={(v) => setParams({ ...params, creativity: v })} />
        <Slider label="Formality" value={params.formality} onChange={(v) => setParams({ ...params, formality: v })} />
        <Slider label="Aggression" value={params.aggression} onChange={(v) => setParams({ ...params, aggression: v })} />
      </div>

      {error && <p className="text-red-400 text-xs">{error}</p>}

      <button
        onClick={() => {/* Apply params */}}
        className="w-full px-4 py-2 bg-indigo-700 hover:bg-indigo-600 text-white text-sm rounded-lg transition-colors"
      >
        Apply Parameters
      </button>
    </div>
  );
}
