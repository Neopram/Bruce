// types/models.ts

export type ModelStatus = "ready" | "loading" | "running" | "error" | "offline" | "warmup";

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  version: string;
  status: ModelStatus;
  type: "llm" | "embedding" | "classifier" | "rl" | "vision" | "speech";
  parameters: {
    size: string;
    quantization?: string;
    contextWindow: number;
    maxTokens: number;
  };
  performance: {
    avgLatency: number;
    throughput: number;
    errorRate: number;
    uptime: number;
  };
  config: Record<string, any>;
  loadedAt?: string;
  lastUsedAt?: string;
}

export interface InferenceRequest {
  modelId: string;
  prompt: string;
  systemPrompt?: string;
  temperature?: number;
  maxTokens?: number;
  topP?: number;
  topK?: number;
  stopSequences?: string[];
  stream?: boolean;
  metadata?: Record<string, any>;
}

export interface InferenceResponse {
  id: string;
  modelId: string;
  output: string;
  tokens: {
    prompt: number;
    completion: number;
    total: number;
  };
  latency: number;
  finishReason: "stop" | "max_tokens" | "error";
  metadata?: Record<string, any>;
  timestamp: string;
}

export interface ModelTrainingConfig {
  modelId: string;
  datasetPath: string;
  epochs: number;
  batchSize: number;
  learningRate: number;
  optimizer: string;
  scheduler?: string;
  earlyStopPatience?: number;
  checkpointInterval?: number;
  evaluationMetrics: string[];
}

export interface ModelTrainingProgress {
  modelId: string;
  epoch: number;
  totalEpochs: number;
  step: number;
  totalSteps: number;
  loss: number;
  metrics: Record<string, number>;
  elapsedTime: number;
  estimatedTimeRemaining: number;
  status: "training" | "evaluating" | "completed" | "failed" | "paused";
}
