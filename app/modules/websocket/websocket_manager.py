import asyncio
import json
import logging
import websockets
from typing import Dict, List
from collections import deque
from app.modules.websocket.data_handler import DataHandler

# Logger configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# WebSocket URLs for real-time market data
EXCHANGE_WS_URIS = {
    "OKX": "wss://ws.okx.com:8443/ws/v5/public",
    "Binance": "wss://stream.binance.com:9443/ws",
    "Bybit": "wss://stream.bybit.com/realtime",
    "KuCoin": "wss://api.kucoin.com/api/v1/bullet-public"
}

# WebSocket message subscription templates
SUBSCRIPTIONS = {
    "OKX": {"op": "subscribe", "args": [{"channel": "books", "instId": "BTC-USDT"}]},
    "Binance": {"method": "SUBSCRIBE", "params": ["btcusdt@depth", "btcusdt@trade"], "id": 1},
    "Bybit": {"op": "subscribe", "args": ["orderBookL2_25.BTCUSDT"]},
    "KuCoin": {"type": "subscribe", "topic": "/market/level2:BTC-USDT", "response": True}
}


class WebSocketManager:
    """
    Advanced WebSocket Manager to handle multiple real-time connections,
    process market data, and distribute updates efficiently.
    """

    def __init__(self, buffer_size: int = 500):
        """
        Initializes the WebSocket Manager.

        Args:
            buffer_size (int): Max buffer size for storing real-time market data.
        """
        self.data_handler = DataHandler(buffer_size=buffer_size)
        self.order_book_data = {exchange: deque(maxlen=buffer_size) for exchange in EXCHANGE_WS_URIS}
        self.trade_data = {exchange: deque(maxlen=buffer_size) for exchange in EXCHANGE_WS_URIS}

    async def connect_to_exchange(self, exchange: str):
        """
        Manages a WebSocket connection to a specific exchange.

        Args:
            exchange (str): The name of the exchange (e.g., "OKX", "Binance").
        """
        uri = EXCHANGE_WS_URIS.get(exchange)
        subscription_message = SUBSCRIPTIONS.get(exchange)
        
        if not uri or not subscription_message:
            logging.error(f"❌ No WebSocket URI or subscription message found for {exchange}.")
            return
        
        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    logging.info(f"🔗 Connected to {exchange} WebSocket.")
                    
                    # Subscribe to market data
                    await websocket.send(json.dumps(subscription_message))

                    while True:
                        message = await websocket.recv()
                        asyncio.create_task(self.process_data(exchange, message))

            except (websockets.exceptions.ConnectionClosed, asyncio.TimeoutError) as e:
                logging.warning(f"🔄 Connection lost to {exchange}. Reconnecting in 5 seconds... {e}")
                await asyncio.sleep(5)

    async def process_data(self, exchange: str, raw_data: str):
        """
        Processes WebSocket data received from exchanges.

        Args:
            exchange (str): The name of the exchange.
            raw_data (str): Raw JSON string received from WebSocket.
        """
        try:
            parsed_data = json.loads(raw_data)

            # Identify whether data is an order book update or a trade event
            if "depth" in parsed_data or "bids" in parsed_data:
                self.order_book_data[exchange].append(parsed_data)
                self.data_handler.store_data({"exchange": exchange, "order_book": parsed_data})

            elif "trade" in parsed_data or "T" in parsed_data:
                self.trade_data[exchange].append(parsed_data)
                self.data_handler.store_data({"exchange": exchange, "trades": parsed_data})

            logging.info(f"📡 Processed new market data from {exchange}")

        except Exception as e:
            logging.error(f"❌ Error processing data from {exchange}: {e}")

    async def manage_connections(self):
        """
        Manages WebSocket connections for all exchanges.
        """
        tasks = [self.connect_to_exchange(exchange) for exchange in EXCHANGE_WS_URIS.keys()]
        await asyncio.gather(*tasks)

    def get_order_book(self) -> Dict[str, List[Dict]]:
        """
        Retrieves the latest order book snapshots.

        Returns:
            Dict[str, List[Dict]]: Order book data per exchange.
        """
        return {exchange: list(self.order_book_data[exchange]) for exchange in self.order_book_data}

    def get_trade_data(self) -> Dict[str, List[Dict]]:
        """
        Retrieves the latest trade data.

        Returns:
            Dict[str, List[Dict]]: Trade execution data per exchange.
        """
        return {exchange: list(self.trade_data[exchange]) for exchange in self.trade_data}


# Example Usage
if __name__ == "__main__":
    websocket_manager = WebSocketManager(buffer_size=500)
    asyncio.run(websocket_manager.manage_connections())
