import asyncio
import aiohttp
import logging
import numpy as np
from app.config.settings import Config
from app.modules.alert_system import AlertSystem

# Logger configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
MAX_RETRIES = 3
LIQUIDITY_THRESHOLD = 500000  # Example threshold for large order detection
VOLUME_SPIKE_PERCENT = 50  # Percentage increase triggering an alert
EXCHANGES = ["OKX", "Binance"]

class VolumeProcessor:
    """
    Handles real-time order book depth analysis, liquidity tracking, and volume-based anomaly detection.
    """

    def __init__(self):
        """
        Initializes the volume processor with multi-exchange support.
        """
        self.alert_system = AlertSystem(
            telegram_config={"bot_token": Config.TELEGRAM_BOT_TOKEN, "chat_id": Config.TELEGRAM_CHAT_ID},
            discord_webhook=Config.DISCORD_WEBHOOK_URL
        )
        self.previous_volume = {}

    async def _fetch_market_data(self, exchange):
        """
        Fetches order book data asynchronously.

        Args:
            exchange (str): The exchange name ("OKX", "Binance").

        Returns:
            dict: Order book data.
        """
        url_map = {
            "OKX": f"https://www.okx.com/api/v5/market/books?instId={Config.TRADING_PAIR.replace('/', '-')}&sz=5",
            "Binance": f"https://api.binance.com/api/v3/depth?symbol={Config.TRADING_PAIR.replace('/', '').upper()}&limit=5"
        }
        url = url_map.get(exchange)

        if not url:
            logging.error(f"❌ Unsupported exchange: {exchange}")
            return {}

        for attempt in range(MAX_RETRIES):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        response.raise_for_status()
                        return await response.json()
            except aiohttp.ClientError as e:
                logging.error(f"🚨 API Request Failed for {exchange}: {e} (Attempt {attempt + 1}/{MAX_RETRIES})")
                await asyncio.sleep(2)

        return {}

    async def analyze_order_book(self, exchange):
        """
        Analyzes order book depth and liquidity.

        Args:
            exchange (str): Exchange name.

        Returns:
            dict: Volume analysis results.
        """
        data = await self._fetch_market_data(exchange)
        if not data:
            return {}

        if exchange == "OKX":
            bids = np.array([float(order[1]) for order in data["data"][0]["bids"]])
            asks = np.array([float(order[1]) for order in data["data"][0]["asks"]])
        elif exchange == "Binance":
            bids = np.array([float(order[1]) for order in data["bids"]])
            asks = np.array([float(order[1]) for order in data["asks"]])
        else:
            return {}

        total_bid_volume = bids.sum()
        total_ask_volume = asks.sum()

        imbalance = total_bid_volume - total_ask_volume
        liquidity_status = "Balanced"

        if total_bid_volume > total_ask_volume * 1.5:
            liquidity_status = "Bullish (Buy Pressure)"
        elif total_ask_volume > total_bid_volume * 1.5:
            liquidity_status = "Bearish (Sell Pressure)"

        return {
            "exchange": exchange,
            "total_bid_volume": total_bid_volume,
            "total_ask_volume": total_ask_volume,
            "imbalance": imbalance,
            "liquidity_status": liquidity_status
        }

    async def detect_volume_anomalies(self, exchange):
        """
        Detects sudden volume spikes or unusual trading activity.

        Args:
            exchange (str): Exchange name.

        Returns:
            bool: True if an anomaly is detected.
        """
        analysis = await self.analyze_order_book(exchange)

        if not analysis:
            return False

        total_volume = analysis["total_bid_volume"] + analysis["total_ask_volume"]
        prev_volume = self.previous_volume.get(exchange, total_volume)

        if abs(total_volume - prev_volume) / prev_volume * 100 > VOLUME_SPIKE_PERCENT:
            alert_msg = f"🚨 Volume Spike Detected on {exchange}! 📊\n" \
                        f"🔹 Buy Volume: {analysis['total_bid_volume']}\n" \
                        f"🔹 Sell Volume: {analysis['total_ask_volume']}\n" \
                        f"🔹 Liquidity Status: {analysis['liquidity_status']}"
            logging.warning(alert_msg)
            await self.alert_system.send_alert(alert_msg, alert_type="telegram")

        self.previous_volume[exchange] = total_volume
        return True

    async def detect_large_orders(self, exchange):
        """
        Identifies large orders in the order book.

        Args:
            exchange (str): Exchange name.

        Returns:
            bool: True if a large order is detected.
        """
        analysis = await self.analyze_order_book(exchange)

        if not analysis:
            return False

        if analysis["total_bid_volume"] > LIQUIDITY_THRESHOLD or analysis["total_ask_volume"] > LIQUIDITY_THRESHOLD:
            alert_msg = f"🚨 Large Order Detected on {exchange}! 📊\n" \
                        f"🔹 Buy Volume: {analysis['total_bid_volume']}\n" \
                        f"🔹 Sell Volume: {analysis['total_ask_volume']}\n" \
                        f"🔹 Liquidity Status: {analysis['liquidity_status']}"
            logging.warning(alert_msg)
            await self.alert_system.send_alert(alert_msg, alert_type="telegram")

        return True

    async def process_volume_data(self):
        """
        Monitors real-time volume and liquidity across exchanges.
        """
        while True:
            logging.info("🔄 Monitoring Order Book Depth & Liquidity...")
            tasks = [self.detect_volume_anomalies(exchange) for exchange in EXCHANGES] + \
                    [self.detect_large_orders(exchange) for exchange in EXCHANGES]

            await asyncio.gather(*tasks)
            await asyncio.sleep(5)  # Adjust delay based on system performance

# Example Usage
if __name__ == "__main__":
    processor = VolumeProcessor()
    asyncio.run(processor.process_volume_data())
