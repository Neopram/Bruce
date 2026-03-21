import React, { useState } from "react";

interface PanelToggle {
  id: string;
  label: string;
  description: string;
  enabled: boolean;
}

const LAYOUTS = [
  { id: "default", label: "Default", cols: "2x3" },
  { id: "focus", label: "Focus Mode", cols: "1x1" },
  { id: "trading", label: "Trading View", cols: "3x2" },
  { id: "analysis", label: "Analysis", cols: "2x2" },
];

const INITIAL_PANELS: PanelToggle[] = [
  { id: "voice", label: "Voice Console", description: "Voice interaction and speech synthesis", enabled: true },
  { id: "token", label: "Token Creator", description: "Deploy crypto tokens across chains", enabled: true },
  { id: "persona", label: "Persona Studio", description: "Customize Bruce's personality parameters", enabled: true },
  { id: "video", label: "Video Report Builder", description: "Generate video market reports", enabled: false },
  { id: "enterprise", label: "Enterprise Hub", description: "Institutional-grade tool access", enabled: true },
  { id: "fullstack", label: "FullStack Builder", description: "AI code generation engine", enabled: true },
  { id: "indicators", label: "Indicators Panel", description: "RSI, MACD, Bollinger, SMA", enabled: false },
  { id: "portfolio", label: "Portfolio Panel", description: "Holdings and allocation overview", enabled: false },
  { id: "memory", label: "Memory Browser", description: "Cognitive memory system", enabled: false },
  { id: "sentiment", label: "Social Sentiment", description: "Fear & Greed, trending topics", enabled: false },
];

export default function VantablackControlPanel() {
  const [ultraDark, setUltraDark] = useState(false);
  const [panels, setPanels] = useState<PanelToggle[]>(INITIAL_PANELS);
  const [layout, setLayout] = useState("default");

  const togglePanel = (id: string) => {
    setPanels((prev) =>
      prev.map((p) => (p.id === id ? { ...p, enabled: !p.enabled } : p))
    );
  };

  const enableAll = () => setPanels((prev) => prev.map((p) => ({ ...p, enabled: true })));
  const disableAll = () => setPanels((prev) => prev.map((p) => ({ ...p, enabled: false })));

  const enabledCount = panels.filter((p) => p.enabled).length;

  return (
    <div className={`rounded-2xl shadow-lg p-6 space-y-5 transition-colors duration-300 ${
      ultraDark ? "bg-black text-gray-200" : "bg-gray-900 text-white"
    }`}>
      <h2 className="text-xl font-bold">Vantablack Control Panel</h2>
      <p className="text-sm text-gray-400">Dashboard appearance and panel configuration</p>

      {/* Ultra Dark Toggle */}
      <div className="bg-gray-800 rounded-xl p-4 flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold">Ultra Dark Mode</p>
          <p className="text-xs text-gray-500">Pure black background for OLED displays</p>
        </div>
        <button onClick={() => setUltraDark(!ultraDark)}
          className={`w-12 h-6 rounded-full relative transition-colors duration-200 ${
            ultraDark ? "bg-cyan-600" : "bg-gray-600"
          }`}>
          <span className={`absolute top-0.5 w-5 h-5 bg-white rounded-full transition-transform duration-200 ${
            ultraDark ? "translate-x-6" : "translate-x-0.5"
          }`} />
        </button>
      </div>

      {/* Layout Selector */}
      <div>
        <h3 className="text-sm font-semibold text-gray-400 mb-2">Layout</h3>
        <div className="grid grid-cols-4 gap-2">
          {LAYOUTS.map((l) => (
            <button key={l.id} onClick={() => setLayout(l.id)}
              className={`p-3 rounded-xl border text-center transition ${
                layout === l.id ? "border-cyan-500 bg-cyan-900/20" : "border-gray-700 bg-gray-800 hover:border-gray-600"
              }`}>
              <p className="text-sm font-medium">{l.label}</p>
              <p className="text-xs text-gray-500">{l.cols}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Panel Visibility */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-gray-400">
            Panel Visibility ({enabledCount}/{panels.length})
          </h3>
          <div className="flex gap-2">
            <button onClick={enableAll} className="text-xs text-cyan-400 hover:text-cyan-300">Enable All</button>
            <button onClick={disableAll} className="text-xs text-gray-500 hover:text-gray-400">Disable All</button>
          </div>
        </div>
        <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
          {panels.map((p) => (
            <div key={p.id}
              className={`flex items-center justify-between p-3 rounded-lg border transition ${
                p.enabled ? "border-gray-700 bg-gray-800" : "border-gray-800 bg-gray-800/30"
              }`}>
              <div className="flex-1 min-w-0 mr-3">
                <p className={`text-sm font-medium ${p.enabled ? "text-white" : "text-gray-600"}`}>{p.label}</p>
                <p className="text-xs text-gray-500 truncate">{p.description}</p>
              </div>
              <button onClick={() => togglePanel(p.id)}
                className={`w-10 h-5 rounded-full relative transition-colors duration-200 flex-shrink-0 ${
                  p.enabled ? "bg-cyan-600" : "bg-gray-600"
                }`}>
                <span className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform duration-200 ${
                  p.enabled ? "translate-x-5" : "translate-x-0.5"
                }`} />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
