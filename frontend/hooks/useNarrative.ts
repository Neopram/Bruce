import { useState, useEffect, useCallback, useRef } from "react";

interface NarrativeState {
  narrative: string;
  isPlaying: boolean;
  isLoading: boolean;
  error: string | null;
  history: string[];
  currentIndex: number;
}

export const useNarrative = (autoFetch: boolean = true, interval: number = 60000) => {
  const [state, setState] = useState<NarrativeState>({
    narrative: "Bruce evolved by analyzing its meta_agent and optimizing execution threads.",
    isPlaying: false,
    isLoading: false,
    error: null,
    history: [],
    currentIndex: -1,
  });
  const intervalRef = useRef<ReturnType<typeof setInterval>>();
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  const fetchNarrative = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      const res = await fetch("/internal/narrative/current");
      if (!res.ok) throw new Error(`Failed to fetch narrative (${res.status})`);
      const data = await res.json();
      const text = data.narrative || data.text || data.message || "";
      if (text) {
        setState((prev) => ({
          ...prev,
          narrative: text,
          history: [...prev.history, text],
          currentIndex: prev.history.length,
          isLoading: false,
        }));
      } else {
        setState((prev) => ({ ...prev, isLoading: false }));
      }
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: err.message || "Failed to fetch narrative",
      }));
    }
  }, []);

  const play = useCallback(() => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(state.narrative);
    utterance.rate = 0.9;
    utterance.pitch = 0.8;
    utterance.onend = () => setState((prev) => ({ ...prev, isPlaying: false }));
    utterance.onerror = () => setState((prev) => ({ ...prev, isPlaying: false }));
    utteranceRef.current = utterance;
    window.speechSynthesis.speak(utterance);
    setState((prev) => ({ ...prev, isPlaying: true }));
  }, [state.narrative]);

  const pause = useCallback(() => {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setState((prev) => ({ ...prev, isPlaying: false }));
  }, []);

  const goToPrevious = useCallback(() => {
    setState((prev) => {
      if (prev.currentIndex <= 0) return prev;
      const newIdx = prev.currentIndex - 1;
      return { ...prev, currentIndex: newIdx, narrative: prev.history[newIdx] };
    });
  }, []);

  const goToNext = useCallback(() => {
    setState((prev) => {
      if (prev.currentIndex >= prev.history.length - 1) return prev;
      const newIdx = prev.currentIndex + 1;
      return { ...prev, currentIndex: newIdx, narrative: prev.history[newIdx] };
    });
  }, []);

  useEffect(() => {
    if (autoFetch) {
      fetchNarrative();
      intervalRef.current = setInterval(fetchNarrative, interval);
    }
    return () => {
      clearInterval(intervalRef.current);
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, [autoFetch, interval, fetchNarrative]);

  return {
    narrative: state.narrative,
    isPlaying: state.isPlaying,
    isLoading: state.isLoading,
    error: state.error,
    history: state.history,
    hasPrevious: state.currentIndex > 0,
    hasNext: state.currentIndex < state.history.length - 1,
    fetchNarrative,
    play,
    pause,
    goToPrevious,
    goToNext,
  };
};
