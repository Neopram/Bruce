// types/api.ts

export interface ApiResponse<T> {
  data: T;
  status: number;
  message: string;
  timestamp: string;
  requestId?: string;
}

export interface ApiError {
  status: number;
  code: string;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
  path?: string;
  requestId?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    pageSize: number;
    totalItems: number;
    totalPages: number;
    hasNext: boolean;
    hasPrevious: boolean;
  };
  status: number;
  message: string;
  timestamp: string;
}

export interface HealthStatus {
  status: "healthy" | "degraded" | "unhealthy";
  version: string;
  uptime: number;
  timestamp: string;
  services: {
    name: string;
    status: "up" | "down" | "degraded";
    latency?: number;
    lastCheck: string;
    details?: Record<string, any>;
  }[];
  system: {
    cpuUsage: number;
    memoryUsage: number;
    diskUsage: number;
    activeConnections: number;
  };
}

export interface WebSocketMessage<T = any> {
  type: string;
  channel: string;
  data: T;
  timestamp: string;
  id?: string;
}

export interface BatchRequest {
  id: string;
  method: "GET" | "POST" | "PUT" | "DELETE";
  path: string;
  body?: any;
}

export interface BatchResponse<T = any> {
  id: string;
  status: number;
  data?: T;
  error?: string;
}
