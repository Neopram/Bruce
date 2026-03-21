import React from "react";
import { useCognition } from "@/hooks/useCognition";

const moodEmoji = {
  curioso: "🤔",
  feliz: "😄",
  serio: "🧐",
  alerta: "⚠️",
  relajado: "😌",
  triste: "😢",
  enfocado: "🎯",
};

export default function BruceAvatar() {
  const { status, loading } = useCognition();

  if (loading || !status) return null;

  const emoji = moodEmoji[status.mood] || "🤖";
  const mensaje = `Hola, estoy en modo "${status.mood}".`;

  return (
    <div className="flex items-center space-x-4 bg-purple-50 p-4 rounded-xl shadow">
      <div className="text-5xl">{emoji}</div>
      <div>
        <p className="text-purple-800 font-medium">{mensaje}</p>
        <p className="text-gray-600 text-sm italic">“{status.last_thought}”</p>
      </div>
    </div>
  );
}