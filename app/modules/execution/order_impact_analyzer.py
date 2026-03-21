import logging
import aiohttp
import asyncio
from app.config.settings import Config

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class OrderImpactAnalyzer:
    """
    AI-Powered Market Impact Analyzer for Large Trade Execution.
    """

    async def fetch_order_book(self):
        """
        Fetches real-time order book data.

        Returns:
            dict: Market order book data.
        """
        url = f"https://www.okx.com/api/v5/market/books?instId={Config.TRADING_PAIR.replace('/', '-')}&sz=5"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logging.error(f"🚨 Failed to fetch order book data: {e}")
            return {}

    async def estimate_market_impact(self, trade_size):
        """
        Estimates market impact based on order book depth.

        Args:
            trade_size (float): Trade size in base currency.

        Returns:
            float: Expected market impact percentage.
        """
        order_book = await self.fetch_order_book()
        if not order_book:
            logging.error("❌ Failed to fetch order book. Cannot estimate market impact.")
            return None

        bid_price = float(order_book["bids"][0][0])
        ask_price = float(order_book["asks"][0][0])
        bid_depth = sum(float(order[1]) for order in order_book["bids"])
        ask_depth = sum(float(order[1]) for order in order_book["asks"])

        market_impact = (trade_size / max(bid_depth, ask_depth)) * (ask_price - bid_price)
        market_impact_percentage = market_impact / ask_price

        logging.info(f"📊 Estimated Market Impact: {market_impact_percentage:.4f} ({trade_size} units)")
        return market_impact_percentage

    async def optimize_trade_execution(self, trade_size):
        """
        Determines the best execution strategy for a given trade size.

        Args:
            trade_size (float): Trade size in base currency.

        Returns:
            str: Suggested execution strategy.
        """
        impact = await self.estimate_market_impact(trade_size)
        if impact is None:
            return "Execution strategy unknown. Market impact assessment failed."

        if impact < 0.002:  # <0.2% market impact → Market Order
            strategy = "Market Order"
        elif impact < 0.005:  # <0.5% market impact → Limit Order
            strategy = "Limit Order"
        else:  # >0.5% market impact → TWAP/VWAP Strategy
            strategy = "TWAP/VWAP Adaptive Execution"

        logging.info(f"🚀 Optimal Execution Strategy: {strategy} for {trade_size} units")
        return strategy

# Example Usage
if __name__ == "__main__":
    impact_analyzer = OrderImpactAnalyzer()
    asyncio.run(impact_analyzer.optimize_trade_execution(trade_size=10.0))
