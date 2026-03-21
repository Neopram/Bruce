import React, { useState, useEffect, useRef } from "react";

interface EvolutionEvent {
  id: number;
  stage: string;
  description: string;
  timestamp: string;
}

interface Props {
  narrative?: string;
}

const MOCK_EVENTS: EvolutionEvent[] = [
  { id: 1, stage: "Genesis", description: "Core cognitive engine initialized", timestamp: "2024-01-01T00:00:00Z" },
  { id: 2, stage: "Awareness", description: "Market pattern recognition activated", timestamp: "2024-02-15T00:00:00Z" },
  { id: 3, stage: "Learning", description: "Reinforcement learning loop established", timestamp: "2024-04-01T00:00:00Z" },
  { id: 4, stage: "Adaptation", description: "Multi-strategy portfolio optimization online", timestamp: "2024-06-20T00:00:00Z" },
  { id: 5, stage: "Mastery", description: "Autonomous decision engine operational", timestamp: "2024-09-10T00:00:00Z" },
];

const EvolutionNarrator: React.FC<Props> = ({ narrative }) => {
  const [events, setEvents] = useState<EvolutionEvent[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [autoPlay, setAutoPlay] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const stats = {
    decisions: 14832,
    knowledge: 2847,
    accuracy: 94.7,
  };

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await fetch("/api/v1/evolution/events");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setEvents(data.events ?? MOCK_EVENTS);
      } catch {
        setEvents(MOCK_EVENTS);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  useEffect(() => {
    if (!autoPlay || events.length === 0) return;
    const timer = setInterval(() => {
      setCurrentIdx((prev) => (prev + 1) % events.length);
    }, 4000);
    return () => clearInterval(timer);
  }, [autoPlay, events.length]);

  useEffect(() => {
    containerRef.current?.scrollTo({ top: containerRef.current.scrollHeight, behavior: "smooth" });
  }, [currentIdx]);

  const currentEvent = events[currentIdx];

  return (
    <div className="bg-gray-900 text-white rounded-2xl shadow-lg p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Evolution Narrator</h2>
        <button onClick={() => setAutoPlay(!autoPlay)}
          className={`px-3 py-1 text-sm rounded transition ${autoPlay ? "bg-green-700 text-green-200" : "bg-gray-700 text-gray-400"}`}>
          {autoPlay ? "Auto-Playing" : "Paused"}
        </button>
      </div>

      {loading && (
        <div className="flex justify-center py-8">
          <div className="animate-spin h-8 w-8 border-4 border-cyan-400 border-t-transparent rounded-full" />
        </div>
      )}

      {error && (
        <div className="bg-red-900/40 border border-red-500 text-red-300 rounded-lg p-3 text-sm">{error}</div>
      )}

      {!loading && (
        <>
          {/* Current stage */}
          {currentEvent && (
            <div className="bg-gradient-to-r from-cyan-900/30 to-purple-900/30 border border-cyan-800/50 rounded-xl p-4 text-center">
              <p className="text-xs text-gray-400 mb-1">Current Stage</p>
              <p className="text-2xl font-bold text-cyan-400">{currentEvent.stage}</p>
              <p className="text-sm text-gray-300 mt-2">{currentEvent.description}</p>
            </div>
          )}

          {/* Timeline */}
          <div ref={containerRef} className="relative pl-6 space-y-3 max-h-48 overflow-y-auto pr-1">
            {events.map((ev, i) => (
              <div key={ev.id} className="relative">
                <div className={`absolute left-[-18px] top-1 w-3 h-3 rounded-full border-2 transition-colors ${
                  i === currentIdx ? "bg-cyan-400 border-cyan-400" : i < currentIdx ? "bg-gray-600 border-gray-500" : "bg-gray-800 border-gray-700"
                }`} />
                {i < events.length - 1 && (
                  <div className={`absolute left-[-13px] top-4 w-0.5 h-full ${i < currentIdx ? "bg-gray-600" : "bg-gray-800"}`} />
                )}
                <div className={`text-sm ${i === currentIdx ? "text-white" : "text-gray-500"}`}>
                  <span className="font-semibold">{ev.stage}</span>
                  <span className="ml-2 text-xs">{new Date(ev.timestamp).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Narrative text */}
          {narrative && (
            <div className="bg-gray-800 rounded-xl p-4 text-sm text-gray-300 italic border-l-2 border-cyan-500">
              {narrative}
            </div>
          )}

          {/* Stats */}
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "Decisions Made", value: stats.decisions.toLocaleString(), color: "text-cyan-400" },
              { label: "Knowledge Learned", value: stats.knowledge.toLocaleString(), color: "text-purple-400" },
              { label: "Accuracy Trend", value: `${stats.accuracy}%`, color: "text-green-400" },
            ].map((s) => (
              <div key={s.label} className="bg-gray-800 rounded-xl p-3 text-center">
                <p className="text-xs text-gray-500">{s.label}</p>
                <p className={`text-lg font-mono font-bold ${s.color}`}>{s.value}</p>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default EvolutionNarrator;
