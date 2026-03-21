import React, { useEffect, useState } from "react";

type Mood = "happy" | "neutral" | "thinking" | "alert" | "sad";

interface Props {
  emotion?: Mood;
}

const MOOD_CONFIG: Record<Mood, { eyeColor: string; mouthPath: string; bgGlow: string }> = {
  happy:    { eyeColor: "#22c55e", mouthPath: "M 30 55 Q 40 68 50 55", bgGlow: "rgba(34,197,94,0.15)" },
  neutral:  { eyeColor: "#06b6d4", mouthPath: "M 30 58 L 50 58",        bgGlow: "rgba(6,182,212,0.1)" },
  thinking: { eyeColor: "#f59e0b", mouthPath: "M 30 58 Q 40 55 50 60",  bgGlow: "rgba(245,158,11,0.12)" },
  alert:    { eyeColor: "#ef4444", mouthPath: "M 30 60 L 35 55 L 45 62 L 50 55", bgGlow: "rgba(239,68,68,0.15)" },
  sad:      { eyeColor: "#8b5cf6", mouthPath: "M 30 62 Q 40 52 50 62",  bgGlow: "rgba(139,92,246,0.15)" },
};

const AvatarFace: React.FC<Props> = ({ emotion = "neutral" }) => {
  const [blinking, setBlinking] = useState(false);
  const [pupilOffset, setPupilOffset] = useState({ x: 0, y: 0 });
  const config = MOOD_CONFIG[emotion] ?? MOOD_CONFIG.neutral;

  // Blink animation
  useEffect(() => {
    const blink = () => {
      setBlinking(true);
      setTimeout(() => setBlinking(false), 150);
    };
    const interval = setInterval(blink, 3000 + Math.random() * 2000);
    return () => clearInterval(interval);
  }, []);

  // Subtle pupil drift for "thinking"
  useEffect(() => {
    if (emotion !== "thinking") { setPupilOffset({ x: 0, y: 0 }); return; }
    const interval = setInterval(() => {
      setPupilOffset({ x: (Math.random() - 0.5) * 3, y: (Math.random() - 0.5) * 2 });
    }, 800);
    return () => clearInterval(interval);
  }, [emotion]);

  const eyeScaleY = blinking ? 0.1 : 1;

  return (
    <div className="bg-gray-900 text-white rounded-2xl shadow-lg p-6 flex flex-col items-center space-y-4">
      <h3 className="text-sm font-semibold text-gray-400">Bruce Avatar</h3>

      <div className="relative" style={{ width: 160, height: 160 }}>
        {/* Glow */}
        <div className="absolute inset-0 rounded-full animate-pulse" style={{ backgroundColor: config.bgGlow }} />

        <svg viewBox="0 0 80 80" className="w-full h-full" style={{ filter: "drop-shadow(0 0 8px rgba(6,182,212,0.3))" }}>
          {/* Head */}
          <circle cx="40" cy="40" r="35" fill="#1f2937" stroke="#374151" strokeWidth="1.5" />
          {/* Inner ring */}
          <circle cx="40" cy="40" r="30" fill="none" stroke={config.eyeColor} strokeWidth="0.5" opacity="0.3" />

          {/* Left Eye */}
          <g transform={`translate(28, 34) scale(1, ${eyeScaleY})`} style={{ transition: "transform 0.1s" }}>
            <ellipse cx="0" cy="0" rx="5" ry="4" fill="#111827" stroke={config.eyeColor} strokeWidth="0.8" />
            <circle cx={pupilOffset.x} cy={pupilOffset.y} r="2" fill={config.eyeColor} />
            <circle cx={pupilOffset.x - 0.8} cy={pupilOffset.y - 1} r="0.6" fill="white" opacity="0.8" />
          </g>

          {/* Right Eye */}
          <g transform={`translate(52, 34) scale(1, ${eyeScaleY})`} style={{ transition: "transform 0.1s" }}>
            <ellipse cx="0" cy="0" rx="5" ry="4" fill="#111827" stroke={config.eyeColor} strokeWidth="0.8" />
            <circle cx={pupilOffset.x} cy={pupilOffset.y} r="2" fill={config.eyeColor} />
            <circle cx={pupilOffset.x - 0.8} cy={pupilOffset.y - 1} r="0.6" fill="white" opacity="0.8" />
          </g>

          {/* Brow lines for alert */}
          {emotion === "alert" && (
            <>
              <line x1="22" y1="27" x2="30" y2="29" stroke={config.eyeColor} strokeWidth="0.8" />
              <line x1="58" y1="27" x2="50" y2="29" stroke={config.eyeColor} strokeWidth="0.8" />
            </>
          )}

          {/* Thinking dots */}
          {emotion === "thinking" && (
            <g opacity="0.5">
              <circle cx="60" cy="22" r="1.5" fill={config.eyeColor} className="animate-pulse" />
              <circle cx="64" cy="18" r="1" fill={config.eyeColor} className="animate-pulse" />
            </g>
          )}

          {/* Mouth */}
          <path d={config.mouthPath} fill="none" stroke={config.eyeColor} strokeWidth="1.2" strokeLinecap="round" />
        </svg>
      </div>

      {/* Mood label */}
      <div className="flex items-center gap-2">
        <span className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: config.eyeColor }} />
        <span className="text-sm capitalize" style={{ color: config.eyeColor }}>{emotion}</span>
      </div>
    </div>
  );
};

export default AvatarFace;
