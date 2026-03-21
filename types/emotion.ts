// types/emotion.ts

export enum EmotionType {
  Neutral = "neutral",
  Focused = "focused",
  Alert = "alert",
  Confident = "confident",
  Cautious = "cautious",
  Euphoric = "euphoric",
  Anxious = "anxious",
  Analytical = "analytical",
  Strategic = "strategic",
  Calm = "calm",
  Aggressive = "aggressive",
  Reflective = "reflective",
}

export interface EmotionState {
  current: EmotionType;
  intensity: number; // 0-1
  valence: number; // -1 to 1 (negative to positive)
  arousal: number; // 0-1 (calm to excited)
  dominance: number; // 0-1 (submissive to dominant)
  secondary?: EmotionType;
  triggers: string[];
  timestamp: string;
}

export interface EmotionTrend {
  emotion: EmotionType;
  values: {
    timestamp: string;
    intensity: number;
    valence: number;
  }[];
  averageIntensity: number;
  dominantPeriods: {
    start: string;
    end: string;
    duration: number;
  }[];
}

export interface EmotionInfluence {
  source: string;
  emotion: EmotionType;
  weight: number;
  description: string;
  decisionImpact: "positive" | "negative" | "neutral";
  affectedStrategies: string[];
  timestamp: string;
}

export interface EmotionProfile {
  baseline: EmotionType;
  tendencies: Record<EmotionType, number>;
  volatility: number;
  resilience: number;
  trends: EmotionTrend[];
  recentInfluences: EmotionInfluence[];
}
