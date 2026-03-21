import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";
import WebSocketClient from "./WebSocketClient";

interface ChatMessage {
  id: string;
  content: string;
  sender: "user" | "ai";
  timestamp: Date;
}

type ConnectionStatus = "connecting" | "connected" | "disconnected" | "reconnecting";

interface WebSocketChatContextValue {
  messages: ChatMessage[];
  sendMessage: (content: string) => void;
  connectionStatus: ConnectionStatus;
  isConnected: boolean;
  clearMessages: () => void;
}

const WebSocketChatContext = createContext<WebSocketChatContextValue | null>(null);

export const useWebSocketChat = (): WebSocketChatContextValue => {
  const ctx = useContext(WebSocketChatContext);
  if (!ctx) throw new Error("useWebSocketChat must be used within WebSocketChatProvider");
  return ctx;
};

interface Props {
  url?: string;
  children: React.ReactNode;
}

const WebSocketChatProvider: React.FC<Props> = ({
  url = `${typeof window !== "undefined" ? (window.location.protocol === "https:" ? "wss:" : "ws:") : "ws:"}//${typeof window !== "undefined" ? window.location.host : "localhost:3000"}/api/ws/chat`,
  children,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("disconnected");
  const clientRef = useRef<WebSocketClient | null>(null);

  useEffect(() => {
    const client = new WebSocketClient({
      url,
      reconnectAttempts: 15,
      reconnectBaseDelay: 1000,
      heartbeatInterval: 25000,
    });

    client.on("connect", () => setConnectionStatus("connected"));
    client.on("disconnect", () => setConnectionStatus("disconnected"));
    client.on("reconnecting", () => setConnectionStatus("reconnecting"));
    client.on("error", (err: any) => console.error("[WS Error]", err));

    client.on("message", (raw: string) => {
      try {
        const data = JSON.parse(raw);
        const msg: ChatMessage = {
          id: data.id || `ws-${Date.now()}`,
          content: data.content || data.message || raw,
          sender: data.sender || "ai",
          timestamp: data.timestamp ? new Date(data.timestamp) : new Date(),
        };
        setMessages((prev) => [...prev, msg]);
      } catch {
        setMessages((prev) => [
          ...prev,
          { id: `ws-${Date.now()}`, content: raw, sender: "ai", timestamp: new Date() },
        ]);
      }
    });

    setConnectionStatus("connecting");
    client.connect();
    clientRef.current = client;

    return () => {
      client.disconnect();
      clientRef.current = null;
    };
  }, [url]);

  const sendMessage = useCallback((content: string) => {
    if (!content.trim()) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      content,
      sender: "user",
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);

    clientRef.current?.send(JSON.stringify({ type: "chat", content, timestamp: new Date().toISOString() }));
  }, []);

  const clearMessages = useCallback(() => setMessages([]), []);

  const isConnected = connectionStatus === "connected";

  return (
    <WebSocketChatContext.Provider value={{ messages, sendMessage, connectionStatus, isConnected, clearMessages }}>
      {/* Connection Status Bar */}
      <div className="relative">
        {connectionStatus !== "connected" && (
          <div
            className={`text-xs text-center py-1 ${
              connectionStatus === "connecting" || connectionStatus === "reconnecting"
                ? "bg-yellow-800 text-yellow-200"
                : "bg-red-800 text-red-200"
            }`}
          >
            {connectionStatus === "connecting" && "Connecting to chat server..."}
            {connectionStatus === "reconnecting" && "Reconnecting..."}
            {connectionStatus === "disconnected" && "Disconnected from chat server"}
          </div>
        )}
        {children}
      </div>
    </WebSocketChatContext.Provider>
  );
};

export default WebSocketChatProvider;
