// types/trading.ts

export type OrderSide = "buy" | "sell";
export type OrderType = "market" | "limit" | "stop" | "stop_limit";
export type OrderStatus = "pending" | "open" | "filled" | "partially_filled" | "cancelled" | "rejected";

export interface Ticker {
  symbol: string;
  price: number;
  change24h: number;
  changePercent24h: number;
  volume24h: number;
  high24h: number;
  low24h: number;
  marketCap?: number;
  lastUpdated: string;
}

export interface OHLCV {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface OrderbookEntry {
  price: number;
  quantity: number;
  total: number;
}

export interface Orderbook {
  symbol: string;
  bids: OrderbookEntry[];
  asks: OrderbookEntry[];
  spread: number;
  timestamp: string;
}

export interface Order {
  id: string;
  symbol: string;
  side: OrderSide;
  type: OrderType;
  status: OrderStatus;
  price: number;
  quantity: number;
  filledQuantity: number;
  averagePrice?: number;
  stopPrice?: number;
  createdAt: string;
  updatedAt: string;
  fees?: number;
}

export interface Position {
  id: string;
  symbol: string;
  side: OrderSide;
  entryPrice: number;
  currentPrice: number;
  quantity: number;
  unrealizedPnl: number;
  realizedPnl: number;
  leverage?: number;
  liquidationPrice?: number;
  openedAt: string;
  margin?: number;
}

export interface TradeHistory {
  id: string;
  symbol: string;
  side: OrderSide;
  price: number;
  quantity: number;
  total: number;
  fees: number;
  pnl?: number;
  executedAt: string;
  orderId: string;
}

export interface Signal {
  id: string;
  symbol: string;
  action: OrderSide;
  confidence: number;
  source: string;
  reason: string;
  targetPrice?: number;
  stopLoss?: number;
  timestamp: string;
  active: boolean;
}

export interface Strategy {
  id: string;
  name: string;
  description: string;
  type: "momentum" | "mean_reversion" | "arbitrage" | "scalping" | "trend_following" | "custom";
  active: boolean;
  parameters: Record<string, any>;
  performance: {
    totalTrades: number;
    winRate: number;
    profitFactor: number;
    sharpeRatio: number;
    maxDrawdown: number;
    totalReturn: number;
  };
  createdAt: string;
  updatedAt: string;
}

export interface Portfolio {
  totalValue: number;
  totalPnl: number;
  totalPnlPercent: number;
  cashBalance: number;
  positions: Position[];
  allocations: {
    symbol: string;
    value: number;
    percentage: number;
  }[];
  lastUpdated: string;
}
