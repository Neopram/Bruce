import React, { useState } from "react";

type InputMode = "text" | "voice" | "image";

interface ModeConfig {
  id: InputMode;
  label: string;
  icon: string;
  description: string;
  statusLabel: string;
}

const MODES: ModeConfig[] = [
  { id: "text", label: "Text", icon: "T", description: "Standard text input with keyboard", statusLabel: "Keyboard active" },
  { id: "voice", label: "Voice", icon: "V", description: "Voice recognition and synthesis", statusLabel: "Microphone active" },
  { id: "image", label: "Image", icon: "I", description: "Screenshot and image analysis", statusLabel: "Camera active" },
];

export default function MultimodalToggle() {
  const [active, setActive] = useState<InputMode>("text");
  const [recording, setRecording] = useState(false);

  const handleModeChange = (mode: InputMode) => {
    setActive(mode);
    if (mode !== "voice") setRecording(false);
  };

  const toggleRecording = () => {
    if (active === "voice") setRecording(!recording);
  };

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-gray-300">Input Mode</h3>
        <span className="text-[10px] text-gray-500">
          {MODES.find((m) => m.id === active)?.statusLabel}
        </span>
      </div>

      {/* Mode Buttons */}
      <div className="flex gap-2">
        {MODES.map((mode) => {
          const isActive = active === mode.id;
          return (
            <button
              key={mode.id}
              onClick={() => handleModeChange(mode.id)}
              className={`flex-1 flex flex-col items-center p-3 rounded-lg border transition-all ${
                isActive
                  ? "border-blue-600 bg-blue-900/30 ring-1 ring-blue-600/30"
                  : "border-gray-700 bg-gray-800 hover:bg-gray-750 hover:border-gray-600"
              }`}
            >
              <div className={`w-10 h-10 rounded-full flex items-center justify-center mb-1.5 text-lg font-bold transition-colors ${
                isActive ? "bg-blue-700 text-white" : "bg-gray-700 text-gray-400"
              }`}>
                {mode.icon}
              </div>
              <span className={`text-xs font-medium ${isActive ? "text-blue-300" : "text-gray-400"}`}>{mode.label}</span>
              <span className="text-[9px] text-gray-500 mt-0.5 text-center">{mode.description}</span>
            </button>
          );
        })}
      </div>

      {/* Voice Recording Indicator */}
      {active === "voice" && (
        <div className="flex items-center justify-center">
          <button
            onClick={toggleRecording}
            className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
              recording
                ? "bg-red-600 hover:bg-red-500 animate-pulse ring-4 ring-red-600/30"
                : "bg-gray-700 hover:bg-gray-600"
            }`}
          >
            <span className="text-white text-lg">{recording ? "||" : "V"}</span>
          </button>
        </div>
      )}

      {/* Image Upload Hint */}
      {active === "image" && (
        <div className="border-2 border-dashed border-gray-700 rounded-lg p-4 text-center">
          <span className="text-xs text-gray-500">Drop an image or click to upload for analysis</span>
        </div>
      )}

      {/* Active Indicator */}
      <div className="flex items-center justify-center gap-1">
        {MODES.map((mode) => (
          <span
            key={mode.id}
            className={`w-1.5 h-1.5 rounded-full transition-colors ${active === mode.id ? "bg-blue-500" : "bg-gray-700"}`}
          />
        ))}
      </div>
    </div>
  );
}
