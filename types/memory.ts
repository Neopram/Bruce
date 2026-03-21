// types/memory.ts

export type MemoryType = "episodic" | "semantic" | "procedural" | "working" | "long_term";
export type MemoryPriority = "low" | "medium" | "high" | "critical";

export interface Memory {
  id: string;
  type: MemoryType;
  content: string;
  summary?: string;
  embedding?: number[];
  tags: string[];
  priority: MemoryPriority;
  accessCount: number;
  relevanceScore: number;
  associations: string[];
  source: string;
  createdAt: string;
  lastAccessedAt: string;
  expiresAt?: string;
  metadata?: Record<string, any>;
}

export interface Episode {
  id: string;
  title: string;
  description: string;
  memories: Memory[];
  context: {
    emotion: string;
    strategy: string;
    marketState?: string;
    userInteraction?: string;
  };
  outcome: {
    success: boolean;
    reward: number;
    learnings: string[];
  };
  startedAt: string;
  completedAt?: string;
  duration?: number;
  parentEpisodeId?: string;
  childEpisodeIds: string[];
}

export interface MemorySearchResult {
  memory: Memory;
  score: number;
  matchedFields: string[];
  highlights: {
    field: string;
    snippet: string;
  }[];
}

export interface MemoryStats {
  totalMemories: number;
  byType: Record<MemoryType, number>;
  byPriority: Record<MemoryPriority, number>;
  averageRelevance: number;
  oldestMemory: string;
  newestMemory: string;
  totalEpisodes: number;
  storageUsed: number;
  compressionRatio: number;
  recentAccesses: {
    timestamp: string;
    memoryId: string;
    accessType: "read" | "write" | "update";
  }[];
}

export interface MemoryConsolidation {
  id: string;
  memoriesProcessed: number;
  memoriesConsolidated: number;
  memoriesPruned: number;
  startedAt: string;
  completedAt?: string;
  status: "running" | "completed" | "failed";
}
