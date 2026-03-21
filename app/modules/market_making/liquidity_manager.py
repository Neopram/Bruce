import asyncio
import logging
import aiohttp
from app.config.settings import Config

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
LIQUIDITY_THRESHOLD = 50000  # Minimum liquidity required in USDT
CHECK_INTERVAL = 10  # Seconds between liquidity checks
MAX_RETRIES = 3  # API retry limit

class LiquidityManager:
    """
    AI-Powered Liquidity Management System for Market Stability.
    """

    def __init__(self):
        """
        Initializes the Liquidity Manager.
        """
        self.dex_liquidity_sources = {
            "Raydium": "https://api.raydium.io/pools",
            "Orca": "https://api.orca.so/pools"
        }
        self.cex_liquidity_sources = {
            "OKX": "https://www.okx.com/api/v5/market/ticker",
            "Binance": "https://api.binance.com/api/v3/ticker/24hr"
        }

    async def fetch_liquidity(self, url):
        """
        Fetches liquidity data from an exchange.

        Args:
            url (str): API endpoint.

        Returns:
            float: Available liquidity.
        """
        for attempt in range(MAX_RETRIES):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        response.raise_for_status()
                        data = await response.json()
                        return float(data["liquidity"])
            except aiohttp.ClientError as e:
                logging.error(f"🚨 API Request Failed: {e} (Attempt {attempt + 1}/{MAX_RETRIES})")
                await asyncio.sleep(2)

        return 0

    async def monitor_liquidity(self):
        """
        Monitors liquidity across CEX and DEX platforms.
        """
        while True:
            for exchange, url in self.cex_liquidity_sources.items():
                liquidity = await self.fetch_liquidity(url)
                if liquidity < LIQUIDITY_THRESHOLD:
                    logging.warning(f"⚠️ Low Liquidity Detected on {exchange}: {liquidity} USDT")
            
            for dex, url in self.dex_liquidity_sources.items():
                liquidity = await self.fetch_liquidity(url)
                if liquidity < LIQUIDITY_THRESHOLD:
                    logging.warning(f"⚠️ Low Liquidity Detected on {dex}: {liquidity} USDT")

            await asyncio.sleep(CHECK_INTERVAL)

# Example Usage
if __name__ == "__main__":
    manager = LiquidityManager()
    asyncio.run(manager.monitor_liquidity())
