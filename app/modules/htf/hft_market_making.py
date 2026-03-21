import logging
import asyncio
import numpy as np
from app.config.settings import Config
from app.modules.websocket.websocket_client import OKXWebSocketClient
from app.modules.order_manager import OrderManager

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
SPREAD_ADJUSTMENT_INTERVAL = 2  # Adjust spread every 2 seconds
MAX_SPREAD = 0.5  # Maximum bid-ask spread in percentage
MIN_SPREAD = 0.05  # Minimum bid-ask spread in percentage
ORDER_BOOK_DEPTH = 10  # Depth of order book to analyze
ARBITRAGE_THRESHOLD = 0.1  # % threshold for executing arbitrage trades
EXECUTION_SPEED = 0.005  # Target execution speed in seconds

class HFTMarketMaker:
    """
    AI-Powered High-Frequency Trading Market Maker for Liquidity Optimization.
    """

    def __init__(self, instrument="BTC/USDT"):
        """
        Initializes the HFT Market Maker.
        """
        self.instrument = instrument
        self.websocket = OKXWebSocketClient(uri=Config.OKX_WEBSOCKET_URI)
        self.order_manager = OrderManager()
        self.bid_price = 0
        self.ask_price = 0

    async def fetch_order_book(self):
        """
        Retrieves real-time order book data.
        """
        order_book = await self.websocket.get_order_book(self.instrument, depth=ORDER_BOOK_DEPTH)
        if "bids" in order_book and "asks" in order_book:
            self.bid_price = float(order_book["bids"][0][0])
            self.ask_price = float(order_book["asks"][0][0])
        return order_book

    async def adjust_bid_ask_spread(self):
        """
        Dynamically adjusts the bid-ask spread based on market volatility.
        """
        order_book = await self.fetch_order_book()
        market_volatility = np.std([float(bid[0]) for bid in order_book["bids"][:ORDER_BOOK_DEPTH]])
        
        adjusted_spread = max(MIN_SPREAD, min(MAX_SPREAD, market_volatility * 0.1))
        self.bid_price = round(self.bid_price * (1 - adjusted_spread / 100), 2)
        self.ask_price = round(self.ask_price * (1 + adjusted_spread / 100), 2)
        
        logging.info(f"📊 Adjusted Spread | Bid: {self.bid_price} | Ask: {self.ask_price}")

    async def execute_market_making_orders(self):
        """
        Places and manages bid-ask orders dynamically.
        """
        await self.order_manager.create_limit_order(self.instrument, "buy", self.bid_price, size=0.1)
        await self.order_manager.create_limit_order(self.instrument, "sell", self.ask_price, size=0.1)
        logging.info("✅ Market making orders placed.")

    async def detect_statistical_arbitrage(self):
        """
        Detects and executes arbitrage opportunities between bid-ask spreads.
        """
        spread = self.ask_price - self.bid_price
        if spread > self.bid_price * ARBITRAGE_THRESHOLD / 100:
            logging.info(f"⚡ Arbitrage Opportunity Detected! Spread: {spread:.2f}")
            await self.order_manager.create_market_order(self.instrument, "buy", size=0.1)
            await self.order_manager.create_market_order(self.instrument, "sell", size=0.1)
        else:
            logging.info(f"⏳ No arbitrage opportunity (Spread: {spread:.2f})")

    async def run_hft_market_making(self):
        """
        Runs the high-frequency market-making strategy continuously.
        """
        logging.info("🚀 Starting AI-Powered HFT Market Making Engine...")
        while True:
            await self.adjust_bid_ask_spread()
            await self.execute_market_making_orders()
            await self.detect_statistical_arbitrage()
            await asyncio.sleep(SPREAD_ADJUSTMENT_INTERVAL)


# Example Usage
if __name__ == "__main__":
    hft_market_maker = HFTMarketMaker()
    asyncio.run(hft_market_maker.run_hft_market_making())
