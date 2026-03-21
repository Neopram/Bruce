import React, { useState } from "react";

interface AvatarOption {
  id: string;
  name: string;
  symbol: string;
  color: string;
}

const AVATARS: AvatarOption[] = [
  { id: "bruce-classic", name: "Bruce Classic", symbol: "BC", color: "from-indigo-600 to-purple-600" },
  { id: "bruce-dark", name: "Dark Knight", symbol: "DK", color: "from-gray-800 to-gray-900" },
  { id: "bruce-neon", name: "Neon Bruce", symbol: "NB", color: "from-cyan-500 to-blue-600" },
  { id: "bruce-fire", name: "Fire Mode", symbol: "FM", color: "from-orange-500 to-red-600" },
  { id: "bruce-ghost", name: "Ghost", symbol: "GH", color: "from-gray-400 to-gray-600" },
  { id: "bruce-gold", name: "Gold Elite", symbol: "GE", color: "from-amber-500 to-yellow-600" },
  { id: "bruce-matrix", name: "Matrix", symbol: "MX", color: "from-green-600 to-emerald-700" },
  { id: "bruce-void", name: "Void", symbol: "VD", color: "from-violet-700 to-fuchsia-800" },
];

export default function AvatarSelector() {
  const [selected, setSelected] = useState<string>("bruce-classic");
  const [saving, setSaving] = useState(false);

  const handleSelect = (id: string) => {
    setSelected(id);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001"}/api/avatar/select`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ avatarId: selected }),
      });
    } catch { /* proceed */ }
    setSaving(false);
  };

  const current = AVATARS.find((a) => a.id === selected);

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-purple-300">Avatar Selector</h2>
        {current && <span className="text-xs text-gray-400">Selected: {current.name}</span>}
      </div>

      {/* Current Preview */}
      <div className="flex justify-center">
        <div className={`w-24 h-24 rounded-full bg-gradient-to-br ${current?.color} flex items-center justify-center shadow-lg ring-2 ring-purple-500/30`}>
          <span className="text-2xl font-bold text-white">{current?.symbol}</span>
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-4 gap-2">
        {AVATARS.map((avatar) => (
          <button
            key={avatar.id}
            onClick={() => handleSelect(avatar.id)}
            className={`flex flex-col items-center p-3 rounded-lg border transition-all ${
              selected === avatar.id
                ? "border-purple-500 bg-purple-900/20 ring-1 ring-purple-500/30"
                : "border-gray-700 bg-gray-800 hover:bg-gray-750"
            }`}
          >
            <div className={`w-10 h-10 rounded-full bg-gradient-to-br ${avatar.color} flex items-center justify-center mb-1.5`}>
              <span className="text-xs font-bold text-white">{avatar.symbol}</span>
            </div>
            <span className="text-[10px] text-gray-300 text-center">{avatar.name}</span>
          </button>
        ))}
      </div>

      <button
        onClick={handleSave}
        disabled={saving}
        className="w-full px-4 py-2 bg-purple-700 hover:bg-purple-600 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm rounded-lg transition-colors"
      >
        {saving ? "Saving..." : "Apply Avatar"}
      </button>
    </div>
  );
}
