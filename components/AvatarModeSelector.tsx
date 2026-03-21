import React, { useState } from "react";

type AvatarMode = "minimal" | "full" | "voice-only";

interface ModeOption {
  id: AvatarMode;
  label: string;
  description: string;
  previewLines: string[];
}

const MODES: ModeOption[] = [
  {
    id: "minimal",
    label: "Minimal",
    description: "Text-only interface. No avatar animations. Low resource usage.",
    previewLines: ["[Bruce]> Analyzing market...", "[Bruce]> BTC bullish bias", "[Bruce]> Risk: 4/10"],
  },
  {
    id: "full",
    label: "Full Avatar",
    description: "Animated avatar with expressions, gestures, and emotional feedback.",
    previewLines: ["Animated face", "Expression tracking", "Gesture responses"],
  },
  {
    id: "voice-only",
    label: "Voice Only",
    description: "Audio interface with voice synthesis and recognition. No visuals.",
    previewLines: ["Voice: ON", "TTS: Active", "STT: Listening..."],
  },
];

export default function AvatarModeSelector() {
  const [mode, setMode] = useState<AvatarMode>("full");
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001"}/api/avatar/mode`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode }),
      });
    } catch { /* proceed */ }
    setSaving(false);
  };

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-5">
      <h2 className="text-lg font-bold text-cyan-300">Avatar Mode</h2>

      <div className="space-y-3">
        {MODES.map((opt) => (
          <label
            key={opt.id}
            className={`flex gap-4 p-4 rounded-lg border cursor-pointer transition-all ${
              mode === opt.id
                ? "border-cyan-600 bg-cyan-900/20 ring-1 ring-cyan-600/30"
                : "border-gray-700 bg-gray-800 hover:bg-gray-750"
            }`}
          >
            <div className="flex items-start pt-0.5">
              <input
                type="radio"
                name="avatar-mode"
                value={opt.id}
                checked={mode === opt.id}
                onChange={() => setMode(opt.id)}
                className="accent-cyan-500 mt-0.5"
              />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-gray-200">{opt.label}</span>
                {mode === opt.id && <span className="text-[10px] bg-cyan-800 text-cyan-200 px-1.5 py-0.5 rounded">ACTIVE</span>}
              </div>
              <p className="text-xs text-gray-400 mt-0.5">{opt.description}</p>

              {/* Preview */}
              <div className="mt-2 bg-gray-950 rounded p-2 border border-gray-700">
                <span className="text-[10px] text-gray-500 block mb-1">Preview</span>
                {opt.previewLines.map((line, i) => (
                  <div key={i} className="text-[11px] text-gray-400 font-mono">{line}</div>
                ))}
              </div>
            </div>
          </label>
        ))}
      </div>

      <button
        onClick={handleSave}
        disabled={saving}
        className="w-full px-4 py-2 bg-cyan-700 hover:bg-cyan-600 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm rounded-lg transition-colors"
      >
        {saving ? "Saving..." : "Apply Mode"}
      </button>
    </div>
  );
}
