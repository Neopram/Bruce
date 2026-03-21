import React, { useState, useEffect, useRef, useCallback } from "react";

interface VoiceNarratorProps {
  initialText?: string;
}

const VoiceNarrator: React.FC<VoiceNarratorProps> = ({ initialText = "" }) => {
  const [text, setText] = useState(initialText);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoice, setSelectedVoice] = useState("");
  const [rate, setRate] = useState(1);
  const [pitch, setPitch] = useState(1);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [queue, setQueue] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const synthRef = useRef(typeof window !== "undefined" ? window.speechSynthesis : null);

  const loadVoices = useCallback(() => {
    const synth = synthRef.current;
    if (!synth) return;
    const available = synth.getVoices();
    setVoices(available);
    if (available.length > 0 && !selectedVoice) {
      setSelectedVoice(available[0].name);
    }
  }, [selectedVoice]);

  useEffect(() => {
    loadVoices();
    if (synthRef.current) {
      synthRef.current.onvoiceschanged = loadVoices;
    }
    return () => { synthRef.current?.cancel(); };
  }, [loadVoices]);

  const speak = (content: string) => {
    const synth = synthRef.current;
    if (!synth) { setError("Speech synthesis not supported"); return; }
    if (!content.trim()) return;

    const utterance = new SpeechSynthesisUtterance(content);
    const voice = voices.find((v) => v.name === selectedVoice);
    if (voice) utterance.voice = voice;
    utterance.rate = rate;
    utterance.pitch = pitch;

    utterance.onstart = () => { setIsSpeaking(true); setIsPaused(false); };
    utterance.onend = () => {
      setIsSpeaking(false);
      setIsPaused(false);
      setQueue((prev) => {
        const next = prev.slice(1);
        if (next.length > 0) {
          setTimeout(() => speak(next[0]), 100);
        }
        return next;
      });
    };
    utterance.onerror = (e) => {
      setError(`Speech error: ${e.error}`);
      setIsSpeaking(false);
    };

    synth.speak(utterance);
  };

  const handlePlay = () => {
    if (isPaused && synthRef.current) {
      synthRef.current.resume();
      setIsPaused(false);
      return;
    }
    speak(text);
  };

  const handlePause = () => {
    synthRef.current?.pause();
    setIsPaused(true);
  };

  const handleStop = () => {
    synthRef.current?.cancel();
    setIsSpeaking(false);
    setIsPaused(false);
    setQueue([]);
  };

  const addToQueue = () => {
    if (!text.trim()) return;
    if (isSpeaking) {
      setQueue((prev) => [...prev, text]);
    } else {
      speak(text);
    }
  };

  return (
    <div className="bg-gray-900 text-white rounded-xl border border-gray-700 p-4 space-y-4">
      <h3 className="text-sm font-semibold text-gray-300">Voice Narrator</h3>

      {/* Text Input */}
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Enter text to narrate..."
        rows={3}
        className="w-full bg-gray-800 text-white rounded-lg px-3 py-2 text-sm placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
      />

      {/* Voice Selector */}
      <div className="flex items-center gap-2">
        <label className="text-xs text-gray-400 shrink-0">Voice:</label>
        <select
          value={selectedVoice}
          onChange={(e) => setSelectedVoice(e.target.value)}
          className="flex-1 bg-gray-800 text-white text-xs rounded px-2 py-1 border border-gray-600 focus:outline-none"
        >
          {voices.map((v) => (
            <option key={v.name} value={v.name}>{v.name} ({v.lang})</option>
          ))}
        </select>
      </div>

      {/* Speed & Pitch */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-gray-400">Speed: {rate.toFixed(1)}x</label>
          <input type="range" min="0.5" max="2" step="0.1" value={rate} onChange={(e) => setRate(parseFloat(e.target.value))}
            className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500" />
        </div>
        <div>
          <label className="text-xs text-gray-400">Pitch: {pitch.toFixed(1)}</label>
          <input type="range" min="0.5" max="2" step="0.1" value={pitch} onChange={(e) => setPitch(parseFloat(e.target.value))}
            className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500" />
        </div>
      </div>

      {/* Controls */}
      <div className="flex gap-2">
        <button onClick={handlePlay} disabled={!text.trim() || (isSpeaking && !isPaused)}
          className="flex-1 py-2 rounded-lg text-sm font-medium bg-green-600 hover:bg-green-700 disabled:bg-gray-700 disabled:text-gray-500 transition">
          {isPaused ? "Resume" : "Play"}
        </button>
        <button onClick={handlePause} disabled={!isSpeaking || isPaused}
          className="flex-1 py-2 rounded-lg text-sm font-medium bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-700 disabled:text-gray-500 transition">
          Pause
        </button>
        <button onClick={handleStop} disabled={!isSpeaking && !isPaused}
          className="flex-1 py-2 rounded-lg text-sm font-medium bg-red-600 hover:bg-red-700 disabled:bg-gray-700 disabled:text-gray-500 transition">
          Stop
        </button>
        <button onClick={addToQueue} disabled={!text.trim()}
          className="py-2 px-3 rounded-lg text-sm font-medium bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 transition">
          +Queue
        </button>
      </div>

      {/* Queue Display */}
      {queue.length > 0 && (
        <div className="text-xs text-gray-400">
          Queue: {queue.length} item{queue.length !== 1 ? "s" : ""} pending
        </div>
      )}

      {/* Status */}
      {isSpeaking && (
        <div className="flex items-center gap-2 text-xs text-green-400">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          {isPaused ? "Paused" : "Speaking..."}
        </div>
      )}

      {error && (
        <div className="bg-red-900/40 border border-red-700 text-red-300 px-3 py-2 rounded text-xs">{error}</div>
      )}
    </div>
  );
};

export default VoiceNarrator;
