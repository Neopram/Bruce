import React, { useState, useMemo } from "react";

interface SliderConfig {
  key: string;
  label: string;
  min: number;
  max: number;
  color: string;
}

const SLIDERS: SliderConfig[] = [
  { key: "riskTolerance", label: "Risk Tolerance", min: 0, max: 100, color: "#ef4444" },
  { key: "creativity", label: "Creativity", min: 0, max: 100, color: "#8b5cf6" },
  { key: "formality", label: "Formality", min: 0, max: 100, color: "#06b6d4" },
  { key: "verbosity", label: "Verbosity", min: 0, max: 100, color: "#22c55e" },
  { key: "aggression", label: "Aggression", min: 0, max: 100, color: "#f59e0b" },
];

const PERSONA_PREVIEWS: Record<string, (vals: Record<string, number>) => string> = {
  riskTolerance: (v) =>
    v.riskTolerance > 70 ? "Bruce takes bold, high-conviction positions with significant leverage." :
    v.riskTolerance > 40 ? "Bruce balances risk and reward with measured position sizing." :
    "Bruce prioritizes capital preservation with conservative hedging.",
  creativity: (v) =>
    v.creativity > 70 ? "Responses include unconventional analogies and creative frameworks." :
    v.creativity > 40 ? "Responses blend standard analysis with occasional creative insights." :
    "Responses are strictly data-driven and analytically structured.",
  aggression: (v) =>
    v.aggression > 70 ? "Bruce pushes for rapid execution and decisive action." :
    v.aggression > 40 ? "Bruce suggests timely action while considering alternatives." :
    "Bruce recommends patience and waiting for optimal entry points.",
};

export default function PersonaStudio() {
  const [values, setValues] = useState<Record<string, number>>({
    riskTolerance: 65,
    creativity: 50,
    formality: 70,
    verbosity: 40,
    aggression: 55,
  });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateValue = (key: string, val: number) => {
    setValues((prev) => ({ ...prev, [key]: val }));
    setSaved(false);
  };

  const preview = useMemo(() => {
    const lines: string[] = [];
    if (PERSONA_PREVIEWS.riskTolerance) lines.push(PERSONA_PREVIEWS.riskTolerance(values));
    if (PERSONA_PREVIEWS.creativity) lines.push(PERSONA_PREVIEWS.creativity(values));
    if (PERSONA_PREVIEWS.aggression) lines.push(PERSONA_PREVIEWS.aggression(values));
    return lines;
  }, [values]);

  const savePersona = async () => {
    setSaving(true);
    setError(null);
    try {
      const res = await fetch("/api/v1/persona/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setSaved(true);
    } catch (e: any) {
      setError(e.message ?? "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-gray-900 text-white rounded-2xl shadow-lg p-6 space-y-5">
      <h2 className="text-xl font-bold">Persona Studio</h2>
      <p className="text-sm text-gray-400">Customize Bruce&apos;s behavioral parameters</p>

      <div className="space-y-4">
        {SLIDERS.map((s) => (
          <div key={s.key}>
            <div className="flex justify-between mb-1">
              <label className="text-sm font-medium">{s.label}</label>
              <span className="text-sm font-mono" style={{ color: s.color }}>{values[s.key]}</span>
            </div>
            <div className="relative">
              <input type="range" min={s.min} max={s.max} value={values[s.key]}
                onChange={(e) => updateValue(s.key, Number(e.target.value))}
                className="w-full h-2 rounded-full appearance-none cursor-pointer"
                style={{
                  background: `linear-gradient(to right, ${s.color} ${values[s.key]}%, #374151 ${values[s.key]}%)`,
                }} />
            </div>
            <div className="flex justify-between text-xs text-gray-600 mt-0.5">
              <span>Low</span><span>High</span>
            </div>
          </div>
        ))}
      </div>

      {/* Preview */}
      <div className="bg-gray-800 rounded-xl p-4 space-y-2">
        <h3 className="text-sm font-semibold text-gray-400">Behavior Preview</h3>
        {preview.map((line, i) => (
          <p key={i} className="text-sm text-gray-300">{line}</p>
        ))}
      </div>

      {/* Save */}
      <button onClick={savePersona} disabled={saving}
        className="w-full py-2.5 rounded-lg bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 disabled:text-gray-500 font-semibold transition">
        {saving ? "Saving..." : saved ? "Saved!" : "Save Persona"}
      </button>

      {error && (
        <div className="bg-red-900/40 border border-red-500 text-red-300 rounded-lg p-3 text-sm">{error}</div>
      )}
    </div>
  );
}
