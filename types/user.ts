// types/user.ts

export type UserRole = "admin" | "trader" | "analyst" | "viewer";

export interface User {
  id: string;
  username: string;
  email: string;
  displayName: string;
  role: UserRole;
  avatarUrl?: string;
  createdAt: string;
  lastLoginAt?: string;
  isActive: boolean;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken?: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  expiresAt?: string;
}

export interface UserProfile {
  user: User;
  preferences: {
    theme: "light" | "dark" | "system";
    language: string;
    timezone: string;
    notifications: {
      email: boolean;
      push: boolean;
      trading: boolean;
      system: boolean;
    };
    dashboard: {
      layout: string;
      widgets: string[];
      refreshInterval: number;
    };
  };
  personality: {
    mode: string;
    voiceEnabled: boolean;
    narrativeStyle: string;
    riskTolerance: "conservative" | "moderate" | "aggressive";
  };
  apiKeys: {
    id: string;
    name: string;
    provider: string;
    maskedKey: string;
    isActive: boolean;
    createdAt: string;
    lastUsedAt?: string;
  }[];
}

export interface UserSession {
  id: string;
  userId: string;
  ipAddress: string;
  userAgent: string;
  startedAt: string;
  lastActivityAt: string;
  expiresAt: string;
  isActive: boolean;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}
