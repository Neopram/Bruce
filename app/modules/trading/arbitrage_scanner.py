import logging
import aiohttp
import asyncio
from app.config.settings import Config

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
CEX_APIS = {
    "binance": "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
    "okx": "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT",
}

DEX_APIS = {
    "raydium": "https://api.raydium.io/pairs",
    "uniswap": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
}

ARBITRAGE_THRESHOLD = 0.5  # Minimum % difference required for arbitrage

class ArbitrageScanner:
    """
    AI-Powered Arbitrage Opportunity Detector.
    """

    async def fetch_price(self, url):
        """
        Fetches price data from an API.

        Args:
            url (str): API endpoint.

        Returns:
            float: Asset price.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return float(data.get("price") or data.get("data", [{}])[0].get("last"))
        except Exception as e:
            logging.error(f"🚨 Failed to fetch price from {url}: {e}")
            return None

    async def detect_arbitrage(self):
        """
        Scans exchanges for arbitrage opportunities.

        Returns:
            dict: Arbitrage opportunities.
        """
        price_data = {}

        # Fetch prices from CEXs
        for exchange, url in CEX_APIS.items():
            price_data[exchange] = await self.fetch_price(url)

        # Fetch prices from DEXs
        for dex, url in DEX_APIS.items():
            price_data[dex] = await self.fetch_price(url)

        # Identify arbitrage opportunities
        arbitrage_opportunities = []
        for src, src_price in price_data.items():
            for dest, dest_price in price_data.items():
                if src != dest and src_price and dest_price:
                    spread = ((dest_price - src_price) / src_price) * 100
                    if spread >= ARBITRAGE_THRESHOLD:
                        arbitrage_opportunities.append({
                            "buy_from": src,
                            "sell_to": dest,
                            "spread": spread
                        })

        logging.info(f"📊 Detected Arbitrage Opportunities: {arbitrage_opportunities}")
        return arbitrage_opportunities

# Example Usage
if __name__ == "__main__":
    scanner = ArbitrageScanner()
    asyncio.run(scanner.detect_arbitrage())
