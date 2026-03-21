// types/chat.ts

/**
 * Roles posibles en la conversación con Bruce.
 */
export type ChatRole =
  | "user"
  | "bruce"
  | "system"
  | "model"
  | "tia"
  | "command"
  | "error"
  | "memory"
  | "debug";

/**
 * Personalidades configurables del sistema Bruce.
 */
export type Personality =
  | "Default"
  | "Guardian"
  | "Shadow"
  | "Genius"
  | "Healer"
  | "Strategist"
  | "Silent"
  | "DoomAI";

/**
 * Un mensaje del chat, completo y compatible con almacenamiento persistente.
 */
export interface ChatMessage {
  id?: string; // UUID opcional para tracking
  role: ChatRole;
  message: string;
  model?: string; // Ej. "phi3", "deepseek"
  personality?: Personality;
  createdAt?: string; // ISO timestamp
  tokens?: number; // Conteo estimado de tokens
  isStreaming?: boolean; // Para mensajes en curso
  systemNote?: string; // Contexto interno del sistema
  origin?: "user" | "auto" | "external" | "retrieved";
  mood?: "neutral" | "focused" | "alert" | "emotional" | "strategic";
}
