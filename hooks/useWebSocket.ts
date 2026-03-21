import { useState, useEffect, useCallback, useRef } from "react";

type WebSocketStatus = "connecting" | "connected" | "disconnected" | "error";

interface WebSocketOptions {
  url: string;
  autoConnect?: boolean;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  onOpen?: (event: Event) => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
  onMessage?: (data: any) => void;
  protocols?: string | string[];
}

interface WebSocketState<T = any> {
  status: WebSocketStatus;
  messages: T[];
  lastMessage: T | null;
  error: string | null;
  reconnectCount: number;
}

export const useWebSocket = <T = any>(options: WebSocketOptions) => {
  const {
    url,
    autoConnect = true,
    reconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
    onOpen,
    onClose,
    onError,
    onMessage,
    protocols,
  } = options;

  const [state, setState] = useState<WebSocketState<T>>({
    status: "disconnected",
    messages: [],
    lastMessage: null,
    error: null,
    reconnectCount: 0,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout>>();
  const reconnectCountRef = useRef(0);
  const intentionalCloseRef = useRef(false);

  const connect = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return;

    try {
      setState((prev) => ({ ...prev, status: "connecting", error: null }));
      const ws = protocols ? new WebSocket(url, protocols) : new WebSocket(url);

      ws.onopen = (event) => {
        setState((prev) => ({
          ...prev,
          status: "connected",
          error: null,
          reconnectCount: 0,
        }));
        reconnectCountRef.current = 0;
        onOpen?.(event);
      };

      ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data) as T;
          setState((prev) => ({
            ...prev,
            messages: [...prev.messages, parsed],
            lastMessage: parsed,
          }));
          onMessage?.(parsed);
        } catch {
          setState((prev) => ({
            ...prev,
            messages: [...prev.messages, event.data as T],
            lastMessage: event.data as T,
          }));
          onMessage?.(event.data);
        }
      };

      ws.onerror = (event) => {
        setState((prev) => ({
          ...prev,
          status: "error",
          error: "WebSocket connection error",
        }));
        onError?.(event);
      };

      ws.onclose = (event) => {
        setState((prev) => ({ ...prev, status: "disconnected" }));
        onClose?.(event);

        if (!intentionalCloseRef.current && reconnect && reconnectCountRef.current < maxReconnectAttempts) {
          reconnectCountRef.current += 1;
          setState((prev) => ({ ...prev, reconnectCount: reconnectCountRef.current }));
          reconnectTimerRef.current = setTimeout(connect, reconnectInterval);
        }
      };

      wsRef.current = ws;
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        status: "error",
        error: err.message || "Failed to connect",
      }));
    }
  }, [url, protocols, reconnect, reconnectInterval, maxReconnectAttempts, onOpen, onClose, onError, onMessage]);

  const disconnect = useCallback(() => {
    intentionalCloseRef.current = true;
    clearTimeout(reconnectTimerRef.current);
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setState((prev) => ({ ...prev, status: "disconnected" }));
  }, []);

  const send = useCallback((data: any) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.warn("WebSocket is not connected");
      return false;
    }
    const payload = typeof data === "string" ? data : JSON.stringify(data);
    wsRef.current.send(payload);
    return true;
  }, []);

  const clearMessages = useCallback(() => {
    setState((prev) => ({ ...prev, messages: [], lastMessage: null }));
  }, []);

  useEffect(() => {
    intentionalCloseRef.current = false;
    if (autoConnect) connect();
    return () => {
      intentionalCloseRef.current = true;
      clearTimeout(reconnectTimerRef.current);
      wsRef.current?.close();
    };
  }, [autoConnect, connect]);

  return {
    status: state.status,
    messages: state.messages,
    lastMessage: state.lastMessage,
    error: state.error,
    reconnectCount: state.reconnectCount,
    isConnected: state.status === "connected",
    connect,
    disconnect,
    send,
    clearMessages,
  };
};
