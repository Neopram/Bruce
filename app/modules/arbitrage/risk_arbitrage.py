import logging
import aiohttp
import asyncio
import numpy as np
from app.config.settings import Config
from app.modules.arbitrage.arbitrage_execution import ArbitrageExecution

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
EXCHANGES = {
    "binance": "https://api.binance.com/api/v3/ticker/price?symbol=",
    "okx": "https://www.okx.com/api/v5/market/ticker?instId="
}

PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

class RiskArbitrage:
    """
    AI-Powered Risk Arbitrage Detector.
    """

    def __init__(self):
        """
        Initializes arbitrage detection system.
        """
        self.execution_engine = ArbitrageExecution()

    async def fetch_prices(self, exchange, pair):
        """
        Fetches price data from an exchange.

        Args:
            exchange (str): Exchange name.
            pair (str): Trading pair.

        Returns:
            float: Price of the asset on the given exchange.
        """
        url = EXCHANGES.get(exchange) + pair
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()
                    if exchange == "okx":
                        return float(data["data"][0]["last"])
                    return float(data["price"])
        except Exception as e:
            logging.error(f"🚨 Failed to fetch price from {exchange}: {e}")
            return None

    async def detect_arbitrage_opportunities(self):
        """
        Scans markets for arbitrage opportunities.

        Returns:
            dict: Arbitrage opportunities detected.
        """
        price_data = {}

        for pair in PAIRS:
            price_data[pair] = {}
            for exchange in EXCHANGES:
                price_data[pair][exchange] = await self.fetch_prices(exchange, pair)

        arbitrage_opportunities = []
        for pair in PAIRS:
            binance_price = price_data[pair]["binance"]
            okx_price = price_data[pair]["okx"]

            if binance_price and okx_price:
                spread = abs(binance_price - okx_price)
                spread_pct = spread / ((binance_price + okx_price) / 2)

                if spread_pct > 0.005:  # 0.5% arbitrage threshold
                    arbitrage_opportunities.append({
                        "pair": pair,
                        "binance_price": binance_price,
                        "okx_price": okx_price,
                        "spread_pct": spread_pct
                    })

        return arbitrage_opportunities

    async def execute_arbitrage_trades(self):
        """
        Executes arbitrage trades based on detected opportunities.
        """
        opportunities = await self.detect_arbitrage_opportunities()
        if not opportunities:
            logging.info("🔍 No arbitrage opportunities found.")
            return

        for opp in opportunities:
            logging.info(f"⚡ Arbitrage Opportunity: {opp}")
            await self.execution_engine.execute_trade(opp)

# Example Usage
if __name__ == "__main__":
    arbitrage_detector = RiskArbitrage()
    asyncio.run(arbitrage_detector.execute_arbitrage_trades())
