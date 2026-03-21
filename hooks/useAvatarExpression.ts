import { useState, useEffect, useCallback, useRef } from "react";

export type AvatarEmotion =
  | "Focused"
  | "Alert"
  | "Calm"
  | "Confident"
  | "Anxious"
  | "Strategic"
  | "Neutral"
  | "Euphoric"
  | "Reflective";

interface AvatarExpressionState {
  emotion: AvatarEmotion;
  intensity: number;
  transitioning: boolean;
  previousEmotion: AvatarEmotion | null;
}

export const useAvatarExpression = () => {
  const [state, setState] = useState<AvatarExpressionState>({
    emotion: "Focused",
    intensity: 0.7,
    transitioning: false,
    previousEmotion: null,
  });
  const transitionTimer = useRef<ReturnType<typeof setTimeout>>();

  const setEmotion = useCallback(
    (newEmotion: AvatarEmotion, intensity: number = 0.7) => {
      setState((prev) => {
        if (prev.emotion === newEmotion && prev.intensity === intensity) return prev;
        clearTimeout(transitionTimer.current);
        return {
          emotion: newEmotion,
          intensity: Math.max(0, Math.min(1, intensity)),
          transitioning: true,
          previousEmotion: prev.emotion,
        };
      });

      transitionTimer.current = setTimeout(() => {
        setState((prev) => ({ ...prev, transitioning: false }));
      }, 600);
    },
    []
  );

  const updateFromEmotionState = useCallback(
    (emotionState: { current?: string; intensity?: number } | null) => {
      if (!emotionState) return;
      const emotionMap: Record<string, AvatarEmotion> = {
        neutral: "Neutral",
        focused: "Focused",
        alert: "Alert",
        confident: "Confident",
        cautious: "Anxious",
        euphoric: "Euphoric",
        anxious: "Anxious",
        analytical: "Strategic",
        strategic: "Strategic",
        calm: "Calm",
        reflective: "Reflective",
      };
      const mapped = emotionMap[emotionState.current || "neutral"] || "Neutral";
      setEmotion(mapped, emotionState.intensity ?? 0.7);
    },
    [setEmotion]
  );

  useEffect(() => {
    return () => clearTimeout(transitionTimer.current);
  }, []);

  return {
    emotion: state.emotion,
    intensity: state.intensity,
    transitioning: state.transitioning,
    previousEmotion: state.previousEmotion,
    setEmotion,
    updateFromEmotionState,
  };
};
