import requests
import logging
import time
import hmac
import hashlib
import base64
import json
from datetime import datetime
from typing import Dict, Any

# Logger configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class DataCollector:
    """
    Collects and processes order book data from OKX with enhanced security, error handling, 
    and real-time processing capabilities.
    """

    def __init__(self, api_key: str, api_secret: str, passphrase: str, base_url: str = "https://www.okx.com"):
        """
        Initializes the DataCollector with API credentials and configuration.

        Args:
            api_key (str): API key for OKX.
            api_secret (str): Secret key for OKX.
            passphrase (str): Passphrase for OKX API.
            base_url (str): Base URL for OKX API (default: "https://www.okx.com").
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.base_url = base_url
        self.session = requests.Session()

    def _generate_signature(self, timestamp: str, method: str, request_path: str, body: str = "") -> str:
        """
        Generates the API signature for secure authentication.
        """
        message = f"{timestamp}{method}{request_path}{body}"
        signature = hmac.new(
            self.api_secret.encode(), message.encode(), hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode()

    def _get_headers(self, method: str, endpoint: str, body: str = "") -> Dict[str, str]:
        """
        Constructs the authentication headers for OKX API requests.
        """
        timestamp = datetime.utcnow().isoformat()
        return {
            "Content-Type": "application/json",
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": self._generate_signature(timestamp, method, endpoint, body),
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase,
        }

    def get_order_book(self, instrument_id: str, depth: int = 10) -> Dict[str, Any]:
        """
        Fetches the order book for a given instrument from OKX.
        """
        endpoint = f"/api/v5/market/books?instId={instrument_id}&sz={depth}"
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers("GET", endpoint)

        for attempt in range(3):  # Retry mechanism for resilience
            try:
                response = self.session.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                if "data" in data:
                    logging.info(f"✅ Order book data retrieved for {instrument_id}: {data}")
                    return data
                else:
                    logging.warning(f"⚠️ Unexpected order book response: {data}")
                    return {"error": "Invalid response format"}
            except requests.exceptions.RequestException as e:
                logging.error(f"❌ Error fetching order book (Attempt {attempt + 1}/3): {e}")
                time.sleep(2)
        return {"error": "Failed to retrieve order book after multiple attempts"}

    def process_order_book(self, order_book: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes the order book data for real-time market analysis.
        """
        try:
            if not order_book or "data" not in order_book:
                raise ValueError("Invalid order book format")
            bids = order_book["data"][0].get("bids", [])
            asks = order_book["data"][0].get("asks", [])
            top_bid = bids[0] if bids else None
            top_ask = asks[0] if asks else None
            processed_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "top_bid": {"price": top_bid[0], "size": top_bid[1]} if top_bid else None,
                "top_ask": {"price": top_ask[0], "size": top_ask[1]} if top_ask else None,
                "spread": round(float(top_ask[0]) - float(top_bid[0]), 6) if top_bid and top_ask else None,
                "bids": bids[:5],
                "asks": asks[:5],
            }
            logging.info(f"🔍 Processed order book data: {json.dumps(processed_data, indent=2)}")
            return processed_data
        except (KeyError, ValueError) as e:
            logging.error(f"❌ Error processing order book data: {e}")
            return {"error": str(e)}

    def fetch_and_process_order_book(self, instrument_id: str, depth: int = 10) -> Dict[str, Any]:
        """
        Combines fetching and processing of order book data in a single method.
        """
        raw_data = self.get_order_book(instrument_id, depth)
        return self.process_order_book(raw_data)

if __name__ == "__main__":
    API_KEY = "your_api_key"
    API_SECRET = "your_api_secret"
    PASSPHRASE = "your_passphrase"
    collector = DataCollector(API_KEY, API_SECRET, PASSPHRASE)
    instrument = "USDT-AED"
    processed_order_book = collector.fetch_and_process_order_book(instrument, depth=10)
    print(json.dumps(processed_order_book, indent=2))
