type EventHandler = (...args: any[]) => void;

interface WebSocketClientOptions {
  url: string;
  reconnectAttempts?: number;
  reconnectBaseDelay?: number;
  heartbeatInterval?: number;
}

class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts: number;
  private reconnectBaseDelay: number;
  private heartbeatInterval: number;
  private currentAttempt = 0;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private messageQueue: string[] = [];
  private listeners: Map<string, Set<EventHandler>> = new Map();
  private _isConnected = false;
  private intentionallyClosed = false;

  constructor(options: WebSocketClientOptions) {
    this.url = options.url;
    this.reconnectAttempts = options.reconnectAttempts ?? 10;
    this.reconnectBaseDelay = options.reconnectBaseDelay ?? 1000;
    this.heartbeatInterval = options.heartbeatInterval ?? 30000;
  }

  get isConnected(): boolean {
    return this._isConnected;
  }

  connect(): void {
    this.intentionallyClosed = false;
    this.currentAttempt = 0;
    this._connect();
  }

  private _connect(): void {
    try {
      this.ws = new WebSocket(this.url);
    } catch (err) {
      this.emit("error", err);
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      this._isConnected = true;
      this.currentAttempt = 0;
      this.startHeartbeat();
      this.flushQueue();
      this.emit("connect");
    };

    this.ws.onmessage = (event: MessageEvent) => {
      const data = event.data;
      if (data === "pong") return;
      this.emit("message", data);
    };

    this.ws.onclose = () => {
      this._isConnected = false;
      this.stopHeartbeat();
      this.emit("disconnect");
      if (!this.intentionallyClosed) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (event: Event) => {
      this.emit("error", event);
    };
  }

  private scheduleReconnect(): void {
    if (this.currentAttempt >= this.reconnectAttempts) {
      this.emit("reconnectFailed");
      return;
    }
    const delay = this.reconnectBaseDelay * Math.pow(2, this.currentAttempt);
    const jittered = delay + Math.random() * 1000;
    this.currentAttempt++;
    this.emit("reconnecting", this.currentAttempt, jittered);
    this.reconnectTimer = setTimeout(() => this._connect(), jittered);
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      if (this._isConnected && this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send("ping");
      }
    }, this.heartbeatInterval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private flushQueue(): void {
    while (this.messageQueue.length > 0) {
      const msg = this.messageQueue.shift()!;
      this.ws?.send(msg);
    }
  }

  send(data: string | object): void {
    const payload = typeof data === "object" ? JSON.stringify(data) : data;
    if (this._isConnected && this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(payload);
    } else {
      this.messageQueue.push(payload);
    }
  }

  on(event: string, handler: EventHandler): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(handler);
  }

  off(event: string, handler: EventHandler): void {
    this.listeners.get(event)?.delete(handler);
  }

  private emit(event: string, ...args: any[]): void {
    this.listeners.get(event)?.forEach((handler) => handler(...args));
  }

  disconnect(): void {
    this.intentionallyClosed = true;
    this.stopHeartbeat();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this._isConnected = false;
  }
}

export default WebSocketClient;
