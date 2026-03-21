import logging
import json
import time
import hmac
import hashlib
import base64
import asyncio
import aiohttp

from app.config.settings import config  # ✅ Usamos la instancia, no la clase
from app.modules.alert_system import AlertSystem

# Logger configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# API Constants
OKX_BASE_URL = "https://www.okx.com"
MAX_RETRIES = 3
RETRY_DELAY = 2


class OrderManager:
    """
    Handles advanced order execution, risk management, and smart routing on OKX.
    """

    def __init__(self):
        """
        Initializes the OrderManager with API credentials and risk management parameters.
        """
        self.api_key = config.OKX_API_KEY
        self.api_secret = config.OKX_SECRET_KEY
        self.passphrase = config.OKX_PASSPHRASE
        self.trading_pair = config.TRADING_PAIR.replace("/", "-")  # OKX format

        self.alert_system = AlertSystem(
            telegram_config={
                "bot_token": getattr(config, "TELEGRAM_BOT_TOKEN", ""),
                "chat_id": getattr(config, "TELEGRAM_CHAT_ID", "")
            },
            discord_webhook=getattr(config, "DISCORD_WEBHOOK_URL", "")
        )

        if self.api_key == "dummy_key":
            logging.warning("⚠️ OrderManager initialized with dummy API credentials. No real trades will be placed.")

    async def _send_request(self, method, endpoint, payload=None):
        """
        Sends an authenticated request to the OKX API.
        """
        url = f"{OKX_BASE_URL}{endpoint}"
        timestamp = str(time.time())
        headers = self._get_headers(timestamp, method, endpoint, json.dumps(payload) if payload else "")

        for attempt in range(MAX_RETRIES):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(method, url, json=payload, headers=headers) as response:
                        response.raise_for_status()
                        return await response.json()
            except aiohttp.ClientError as e:
                logging.error(f"API Request Failed: {e} (Attempt {attempt + 1}/{MAX_RETRIES})")
                await asyncio.sleep(RETRY_DELAY)

        self.alert_system.send_alert(f"❌ API failure on endpoint: {endpoint}", alert_type="telegram")
        return {"error": "Max retries reached"}

    async def create_order(self, side, size, price=None, order_type="limit", leverage=1):
        """
        Places a single order on OKX.
        """
        if order_type == "limit" and price is None:
            raise ValueError("Price is required for limit orders.")

        payload = {
            "instId": self.trading_pair,
            "side": side,
            "ordType": order_type,
            "sz": str(size),
            "tdMode": "cross" if leverage > 1 else "cash",
            "lever": str(leverage)
        }

        if order_type == "limit":
            payload["px"] = str(price)
        if order_type == "post_only":
            payload["postOnly"] = True

        response = await self._send_request("POST", "/api/v5/trade/order", payload)

        if "error" in response:
            self.alert_system.send_alert(f"❌ Order Failed: {json.dumps(response)}", alert_type="telegram")

        return response

    async def batch_create_orders(self, orders):
        """
        Places multiple orders in a batch.
        """
        payload = {"orders": orders}
        response = await self._send_request("POST", "/api/v5/trade/batch-orders", payload)

        if "error" in response:
            self.alert_system_
