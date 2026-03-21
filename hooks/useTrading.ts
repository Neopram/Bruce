import { useState, useEffect, useCallback, useRef } from "react";
import { useApiClient } from "@/hooks/useApi";
import type { Portfolio, Position, Order, Signal, TradeHistory } from "@/types/trading";

interface TradingState {
  portfolio: Portfolio | null;
  positions: Position[];
  orders: Order[];
  signals: Signal[];
  recentTrades: TradeHistory[];
  isLoading: boolean;
  error: string | null;
  lastUpdated: string | null;
}

interface UseTradingOptions {
  autoFetch?: boolean;
  pollInterval?: number;
  enableRealTime?: boolean;
}

export const useTrading = (options: UseTradingOptions = {}) => {
  const { autoFetch = true, pollInterval = 15000, enableRealTime = false } = options;
  const client = useApiClient();
  const pollRef = useRef<ReturnType<typeof setInterval>>();
  const wsRef = useRef<WebSocket | null>(null);

  const [state, setState] = useState<TradingState>({
    portfolio: null,
    positions: [],
    orders: [],
    signals: [],
    recentTrades: [],
    isLoading: false,
    error: null,
    lastUpdated: null,
  });

  const fetchPortfolio = useCallback(async () => {
    try {
      const data = await client.get<Portfolio>("/api/trading/portfolio");
      setState((prev) => ({ ...prev, portfolio: data }));
    } catch (err: any) {
      console.error("Portfolio fetch error:", err.message);
    }
  }, [client]);

  const fetchPositions = useCallback(async () => {
    try {
      const data = await client.get<Position[]>("/api/trading/positions");
      setState((prev) => ({ ...prev, positions: data }));
    } catch (err: any) {
      console.error("Positions fetch error:", err.message);
    }
  }, [client]);

  const fetchOrders = useCallback(async () => {
    try {
      const data = await client.get<Order[]>("/api/trading/orders");
      setState((prev) => ({ ...prev, orders: data }));
    } catch (err: any) {
      console.error("Orders fetch error:", err.message);
    }
  }, [client]);

  const fetchSignals = useCallback(async () => {
    try {
      const data = await client.get<Signal[]>("/api/trading/signals");
      setState((prev) => ({ ...prev, signals: data }));
    } catch (err: any) {
      console.error("Signals fetch error:", err.message);
    }
  }, [client]);

  const fetchAll = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      await Promise.allSettled([
        fetchPortfolio(),
        fetchPositions(),
        fetchOrders(),
        fetchSignals(),
      ]);
      setState((prev) => ({
        ...prev,
        isLoading: false,
        lastUpdated: new Date().toISOString(),
      }));
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: err.message || "Failed to fetch trading data",
      }));
    }
  }, [fetchPortfolio, fetchPositions, fetchOrders, fetchSignals]);

  const placeOrder = useCallback(
    async (order: {
      symbol: string;
      side: "buy" | "sell";
      type: string;
      quantity: number;
      price?: number;
    }) => {
      const data = await client.post("/api/trading/orders", order);
      await fetchOrders();
      return data;
    },
    [client, fetchOrders]
  );

  const cancelOrder = useCallback(
    async (orderId: string) => {
      await client.post(`/api/trading/orders/${orderId}/cancel`, {});
      await fetchOrders();
    },
    [client, fetchOrders]
  );

  const closePosition = useCallback(
    async (positionId: string) => {
      await client.post(`/api/trading/positions/${positionId}/close`, {});
      await fetchPositions();
      await fetchPortfolio();
    },
    [client, fetchPositions, fetchPortfolio]
  );

  // WebSocket real-time updates
  useEffect(() => {
    if (!enableRealTime || typeof window === "undefined") return;

    const wsUrl = (process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8001") + "/ws/trading";
    try {
      const ws = new WebSocket(wsUrl);
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === "position_update") {
            setState((prev) => ({
              ...prev,
              positions: prev.positions.map((p) =>
                p.id === msg.data.id ? { ...p, ...msg.data } : p
              ),
            }));
          } else if (msg.type === "order_update") {
            fetchOrders();
          } else if (msg.type === "signal") {
            setState((prev) => ({
              ...prev,
              signals: [msg.data, ...prev.signals].slice(0, 50),
            }));
          }
        } catch {
          // ignore parse errors
        }
      };
      wsRef.current = ws;
    } catch {
      // WebSocket not available
    }

    return () => {
      wsRef.current?.close();
    };
  }, [enableRealTime, fetchOrders]);

  // Polling
  useEffect(() => {
    if (autoFetch) {
      fetchAll();
      pollRef.current = setInterval(fetchAll, pollInterval);
    }
    return () => clearInterval(pollRef.current);
  }, [autoFetch, pollInterval, fetchAll]);

  return {
    ...state,
    fetchAll,
    fetchPortfolio,
    fetchPositions,
    fetchOrders,
    fetchSignals,
    placeOrder,
    cancelOrder,
    closePosition,
  };
};
