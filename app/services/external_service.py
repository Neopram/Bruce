import aiohttp
import asyncio
import time
import logging
import hmac
import hashlib
import base64
from cachetools import TTLCache
from app.config.settings import Config

# Logger configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
MAX_RETRIES = 5
BASE_RETRY_DELAY = 2  # Base delay in seconds for exponential backoff
CACHE_TTL = 30  # Cache expiry time in seconds


class ExternalService:
    """
    Handles secure external API requests with failover, authentication, retry logic, caching, and load balancing.
    """

    def __init__(self, api_urls=None, max_retries=MAX_RETRIES, timeout=5):
        """
        Initializes the external API service.

        Args:
            api_urls (list, optional): List of API endpoints for failover.
            max_retries (int): Maximum retry attempts for failed requests.
            timeout (int): Timeout for API requests in seconds.
        """
        self.api_urls = api_urls or Config.EXTERNAL_API_URLS
        self.max_retries = max_retries
        self.timeout = timeout
        self.cache = TTLCache(maxsize=100, ttl=CACHE_TTL)
        self.failed_attempts = {url: 0 for url in self.api_urls}  # Tracks consecutive failures

    def _generate_hmac_signature(self, timestamp, method, endpoint, body=""):
        """
        Generates an HMAC-SHA256 signature for API authentication.

        Args:
            timestamp (str): Request timestamp.
            method (str): HTTP method.
            endpoint (str): API endpoint.
            body (str): Request body (default empty).

        Returns:
            str: Base64-encoded HMAC signature.
        """
        message = f"{timestamp}{method.upper()}{endpoint}{body}"
        signature = hmac.new(Config.API_SECRET.encode(), message.encode(), hashlib.sha256).digest()
        return base64.b64encode(signature).decode()

    async def _fetch(self, session, url, headers):
        """
        Fetch data asynchronously from an API with error handling.

        Args:
            session (aiohttp.ClientSession): HTTP session.
            url (str): API request URL.
            headers (dict): Request headers.

        Returns:
            dict: API response data or None if request fails.
        """
        try:
            async with session.get(url, headers=headers, timeout=self.timeout) as response:
                if response.status == 429:
                    logging.warning("⚠️ API rate limited. Retrying with backoff...")
                    await asyncio.sleep(BASE_RETRY_DELAY)
                    return None

                if response.status >= 500:
                    logging.error(f"❌ API server error ({response.status}) at {url}")
                    return None

                return await response.json()

        except asyncio.TimeoutError:
            logging.error(f"🚨 API request timeout for {url}")
            return None

        except Exception as e:
            logging.error(f"❌ Error fetching data from {url}: {e}")
            return None

    async def call_api(self, endpoint, method="GET"):
        """
        Makes an authenticated API request with retry logic, failover, and caching.

        Args:
            endpoint (str): API endpoint path.
            method (str): HTTP method (default: GET).

        Returns:
            dict: API response data or None if all retries fail.
        """
        async with aiohttp.ClientSession() as session:
            for attempt in range(self.max_retries):
                for api_url in self.api_urls:
                    # Skip failed API endpoints to prevent unnecessary retries
                    if self.failed_attempts[api_url] >= 3:
                        logging.warning(f"⛔ Skipping {api_url} due to repeated failures")
                        continue

                    full_url = f"{api_url}{endpoint}"
                    timestamp = str(int(time.time()))
                    headers = {
                        "Content-Type": "application/json",
                        "API-KEY": Config.API_KEY,
                        "API-SIGNATURE": self._generate_hmac_signature(timestamp, method, endpoint),
                        "API-TIMESTAMP": timestamp,
                    }

                    # Check cache before making the request
                    if full_url in self.cache:
                        logging.info(f"✅ Returning cached data for {full_url}")
                        return self.cache[full_url]

                    logging.info(f"🔄 Attempting API call: {full_url} (Try {attempt + 1}/{self.max_retries})")
                    result = await self._fetch(session, full_url, headers)

                    if result:
                        self.cache[full_url] = result  # Cache successful responses
                        self.failed_attempts[api_url] = 0  # Reset failure count
                        return result

                # Apply exponential backoff for retrying requests
                retry_delay = BASE_RETRY_DELAY * (2 ** attempt)
                logging.warning(f"🔁 Retrying API call in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)

        logging.error(f"🚨 API request failed after {self.max_retries} retries.")
        return None


# Example Usage
if __name__ == "__main__":
    api_handler = ExternalService(
        api_urls=["https://api.exchange1.com", "https://api.exchange2.com"]
    )

    loop = asyncio.get_event_loop()
    response = loop.run_until_complete(api_handler.call_api("/market/prices"))

    if response:
        print("📊 API Response:", response)
    else:
        print("❌ API request failed.")
