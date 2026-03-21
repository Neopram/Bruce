import React, { useState, useEffect, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

type Mood = "neutral" | "happy" | "focused" | "stressed" | "excited" | "sad";

const MOOD_CONFIG: Record<Mood, { eyeColor: string; mouthPath: string; bgGlow: string; animation: string; label: string }> = {
  neutral: { eyeColor: "#60a5fa", mouthPath: "M 35,58 Q 50,60 65,58", bgGlow: "shadow-blue-500/20", animation: "", label: "Neutral" },
  happy: { eyeColor: "#34d399", mouthPath: "M 35,55 Q 50,68 65,55", bgGlow: "shadow-green-500/30", animation: "animate-bounce", label: "Happy" },
  focused: { eyeColor: "#a78bfa", mouthPath: "M 38,58 L 62,58", bgGlow: "shadow-purple-500/20", animation: "", label: "Focused" },
  stressed: { eyeColor: "#f87171", mouthPath: "M 35,62 Q 50,52 65,62", bgGlow: "shadow-red-500/30", animation: "animate-pulse", label: "Stressed" },
  excited: { eyeColor: "#fbbf24", mouthPath: "M 32,53 Q 50,72 68,53", bgGlow: "shadow-yellow-500/30", animation: "animate-bounce", label: "Excited" },
  sad: { eyeColor: "#93c5fd", mouthPath: "M 35,62 Q 50,55 65,62", bgGlow: "shadow-blue-400/20", animation: "", label: "Sad" },
};

export default function AvatarPhysicalization() {
  const [mood, setMood] = useState<Mood>("neutral");
  const [loading, setLoading] = useState(true);
  const [blinking, setBlinking] = useState(false);

  const fetchMood = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/bruce-api/emotion/state/default`);
      if (!res.ok) throw new Error();
      const data = await res.json();
      const m = data.dominant || data.mood || "neutral";
      if (m in MOOD_CONFIG) setMood(m as Mood);
    } catch { /* keep current mood */ }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchMood();
    const interval = setInterval(fetchMood, 5000);
    return () => clearInterval(interval);
  }, [fetchMood]);

  // Blink animation
  useEffect(() => {
    const blinkInterval = setInterval(() => {
      setBlinking(true);
      setTimeout(() => setBlinking(false), 150);
    }, 3000 + Math.random() * 2000);
    return () => clearInterval(blinkInterval);
  }, []);

  const config = MOOD_CONFIG[mood];

  if (loading) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 animate-pulse flex flex-col items-center">
        <div className="w-32 h-32 bg-gray-800 rounded-full" />
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-4">
      <h2 className="text-lg font-bold text-blue-300 text-center">Avatar</h2>

      {/* Avatar Face */}
      <div className="flex justify-center">
        <div className={`relative w-36 h-36 rounded-full bg-gradient-to-b from-gray-800 to-gray-900 shadow-lg ${config.bgGlow} shadow-2xl border-2 border-gray-600 ${config.animation}`}>
          <svg viewBox="0 0 100 100" className="w-full h-full">
            {/* Face outline glow */}
            <circle cx="50" cy="50" r="46" fill="none" stroke={config.eyeColor} strokeWidth="0.5" opacity="0.3" />

            {/* Left eye */}
            {blinking ? (
              <line x1="30" y1="38" x2="42" y2="38" stroke={config.eyeColor} strokeWidth="2" strokeLinecap="round" />
            ) : (
              <ellipse cx="36" cy="38" rx="6" ry="5" fill={config.eyeColor} opacity="0.9">
                <animate attributeName="opacity" values="0.9;1;0.9" dur="2s" repeatCount="indefinite" />
              </ellipse>
            )}

            {/* Right eye */}
            {blinking ? (
              <line x1="58" y1="38" x2="70" y2="38" stroke={config.eyeColor} strokeWidth="2" strokeLinecap="round" />
            ) : (
              <ellipse cx="64" cy="38" rx="6" ry="5" fill={config.eyeColor} opacity="0.9">
                <animate attributeName="opacity" values="0.9;1;0.9" dur="2s" repeatCount="indefinite" />
              </ellipse>
            )}

            {/* Pupils */}
            {!blinking && (
              <>
                <circle cx="37" cy="38" r="2.5" fill="#111827" />
                <circle cx="65" cy="38" r="2.5" fill="#111827" />
              </>
            )}

            {/* Mouth */}
            <path d={config.mouthPath} fill="none" stroke={config.eyeColor} strokeWidth="2" strokeLinecap="round" opacity="0.8" />

            {/* Eyebrows for stressed */}
            {mood === "stressed" && (
              <>
                <line x1="28" y1="30" x2="42" y2="28" stroke={config.eyeColor} strokeWidth="1.5" opacity="0.6" />
                <line x1="58" y1="28" x2="72" y2="30" stroke={config.eyeColor} strokeWidth="1.5" opacity="0.6" />
              </>
            )}
          </svg>
        </div>
      </div>

      {/* Mood Label */}
      <div className="text-center">
        <span className="text-sm font-semibold" style={{ color: config.eyeColor }}>{config.label}</span>
      </div>

      {/* Mood Selector */}
      <div className="flex flex-wrap justify-center gap-1.5">
        {(Object.keys(MOOD_CONFIG) as Mood[]).map((m) => (
          <button
            key={m}
            onClick={() => setMood(m)}
            className={`text-[10px] px-2 py-1 rounded transition-colors ${
              mood === m ? "bg-blue-800 text-blue-200" : "bg-gray-800 text-gray-400 hover:bg-gray-700"
            }`}
          >
            {m}
          </button>
        ))}
      </div>
    </div>
  );
}
