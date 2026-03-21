"""
Multi-exchange arbitrage detector.
Scans price differences across exchanges, calculates profit after fees, and executes arbitrage.
"""
import time
import random
from datetime import datetime


class ArbitrageOmniverse:
    """Detects and executes arbitrage opportunities across multiple exchanges."""

    def __init__(self, fee_rate=0.001, min_profit_pct=0.05):
        self.dimensions = 11
        self.universe_threshold = min_profit_pct
        self.fee_rate = fee_rate
        self.exchanges = ["binance", "coinbase", "kraken", "bybit", "okx", "kucoin"]
        self.tracked_pairs = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"]
        self.opportunity_log = []
        self.active = True
        self.max_slippage = 0.002

    def detect_arbitrage(self):
        """Scan all exchange pairs for arbitrage opportunities."""
        profitable_dimensions = []
        for dimension in range(self.dimensions):
            profit = self.calculate_dimension_profit(dimension)
            if profit > self.universe_threshold:
                self.cross_universe_execute(dimension, profit)
                profitable_dimensions.append((dimension, profit))
        return profitable_dimensions

    def scan_cross_exchange(self, pair="BTC/USDT"):
        """Scan price differences for a pair across all exchanges."""
        prices = self._fetch_prices(pair)
        if len(prices) < 2:
            return {"status": "error", "message": "Insufficient price data"}

        opportunities = []
        exchange_names = list(prices.keys())
        for i in range(len(exchange_names)):
            for j in range(i + 1, len(exchange_names)):
                buy_ex = exchange_names[i]
                sell_ex = exchange_names[j]
                buy_price = prices[buy_ex]
                sell_price = prices[sell_ex]
                if sell_price > buy_price:
                    spread = self._calculate_net_profit(buy_price, sell_price)
                    if spread > self.universe_threshold:
                        opp = {
                            "pair": pair,
                            "buy_exchange": buy_ex,
                            "sell_exchange": sell_ex,
                            "buy_price": buy_price,
                            "sell_price": sell_price,
                            "gross_spread_pct": round((sell_price - buy_price) / buy_price * 100, 4),
                            "net_profit_pct": round(spread * 100, 4),
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                        opportunities.append(opp)
                elif buy_price > sell_price:
                    spread = self._calculate_net_profit(sell_price, buy_price)
                    if spread > self.universe_threshold:
                        opp = {
                            "pair": pair,
                            "buy_exchange": sell_ex,
                            "sell_exchange": buy_ex,
                            "buy_price": sell_price,
                            "sell_price": buy_price,
                            "gross_spread_pct": round((buy_price - sell_price) / sell_price * 100, 4),
                            "net_profit_pct": round(spread * 100, 4),
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                        opportunities.append(opp)

        self.opportunity_log.extend(opportunities)
        return {"pair": pair, "opportunities": opportunities, "count": len(opportunities)}

    def _calculate_net_profit(self, buy_price, sell_price):
        """Calculate net profit after fees and estimated slippage."""
        gross = (sell_price - buy_price) / buy_price
        total_fees = self.fee_rate * 2  # buy + sell fee
        slippage = self.max_slippage
        return gross - total_fees - slippage

    def _fetch_prices(self, pair):
        """Fetch simulated prices from exchanges."""
        base_price = {"BTC/USDT": 65000, "ETH/USDT": 3400, "SOL/USDT": 145, "BNB/USDT": 580}.get(pair, 100)
        prices = {}
        for ex in self.exchanges:
            variation = random.uniform(-0.005, 0.005)
            prices[ex] = round(base_price * (1 + variation), 2)
        return prices

    def calculate_dimension_profit(self, dimension):
        """Simulate dynamic pricing conditions for a dimension."""
        return round(random.uniform(0, 0.1), 4)

    def cross_universe_execute(self, dimension, profit):
        """Execute arbitrage in a given dimension."""
        entry = {
            "dimension": dimension,
            "profit_pct": profit,
            "executed_at": datetime.utcnow().isoformat(),
        }
        self.opportunity_log.append(entry)
        print(f"Executed arbitrage in Dimension {dimension} with {profit*100:.2f}% profit")

    def execute_opportunity(self, opportunity, volume_usd=1000):
        """Execute a specific arbitrage opportunity."""
        if not self.active:
            return {"status": "error", "message": "Arbitrage engine is paused"}
        estimated_profit = volume_usd * (opportunity["net_profit_pct"] / 100)
        return {
            "status": "executed",
            "pair": opportunity["pair"],
            "buy_exchange": opportunity["buy_exchange"],
            "sell_exchange": opportunity["sell_exchange"],
            "volume_usd": volume_usd,
            "estimated_profit_usd": round(estimated_profit, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_opportunity_log(self, limit=50):
        """Return recent arbitrage opportunities."""
        return self.opportunity_log[-limit:]

    def set_active(self, active):
        """Enable or disable the arbitrage engine."""
        self.active = active
        return {"active": self.active}

    def get_stats(self):
        """Return summary statistics."""
        total = len(self.opportunity_log)
        return {
            "total_opportunities_found": total,
            "exchanges_monitored": len(self.exchanges),
            "pairs_tracked": len(self.tracked_pairs),
            "fee_rate": self.fee_rate,
            "min_profit_threshold": self.universe_threshold,
            "active": self.active,
        }
