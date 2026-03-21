import { useState, useEffect, useCallback, useRef } from "react";

interface StrategyRecommendation {
  id: string;
  title: string;
  description: string;
  priority: "low" | "medium" | "high" | "critical";
  confidence: number;
  category: string;
  timestamp: string;
}

interface StrategicMindState {
  strategies: string[];
  recommendations: StrategyRecommendation[];
  isLoading: boolean;
  error: string | null;
  lastUpdated: string | null;
  activeObjective: string | null;
}

export const useStrategicMind = (pollInterval: number = 30000) => {
  const [state, setState] = useState<StrategicMindState>({
    strategies: [
      "Refactor memory module",
      "Deploy LLM fallback bridge",
      "Evaluate simulation outcomes",
    ],
    recommendations: [],
    isLoading: false,
    error: null,
    lastUpdated: null,
    activeObjective: null,
  });
  const pollingRef = useRef<ReturnType<typeof setInterval>>();

  const fetchStrategies = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      const res = await fetch("/internal/strategic/recommendations");
      if (!res.ok) throw new Error(`Strategy fetch failed (${res.status})`);
      const data = await res.json();

      setState((prev) => ({
        ...prev,
        strategies: data.strategies || prev.strategies,
        recommendations: (data.recommendations || []).map((r: any, i: number) => ({
          id: r.id || `rec-${i}`,
          title: r.title || r.name || "Unnamed",
          description: r.description || "",
          priority: r.priority || "medium",
          confidence: r.confidence || 0.5,
          category: r.category || "general",
          timestamp: r.timestamp || new Date().toISOString(),
        })),
        isLoading: false,
        lastUpdated: new Date().toISOString(),
      }));
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: err.message || "Failed to fetch strategies",
      }));
    }
  }, []);

  const setActiveObjective = useCallback((objective: string | null) => {
    setState((prev) => ({ ...prev, activeObjective: objective }));
  }, []);

  const addStrategy = useCallback((strategy: string) => {
    setState((prev) => ({
      ...prev,
      strategies: [...prev.strategies, strategy],
    }));
  }, []);

  const removeStrategy = useCallback((index: number) => {
    setState((prev) => ({
      ...prev,
      strategies: prev.strategies.filter((_, i) => i !== index),
    }));
  }, []);

  const executeRecommendation = useCallback(async (id: string) => {
    try {
      const res = await fetch("/internal/strategic/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ recommendationId: id }),
      });
      if (!res.ok) throw new Error("Execution failed");
      await fetchStrategies();
    } catch (err: any) {
      setState((prev) => ({ ...prev, error: err.message }));
    }
  }, [fetchStrategies]);

  useEffect(() => {
    fetchStrategies();
    pollingRef.current = setInterval(fetchStrategies, pollInterval);
    return () => clearInterval(pollingRef.current);
  }, [pollInterval, fetchStrategies]);

  return {
    strategies: state.strategies,
    recommendations: state.recommendations,
    isLoading: state.isLoading,
    error: state.error,
    lastUpdated: state.lastUpdated,
    activeObjective: state.activeObjective,
    fetchStrategies,
    setActiveObjective,
    addStrategy,
    removeStrategy,
    executeRecommendation,
  };
};
