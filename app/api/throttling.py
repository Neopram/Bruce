import time
import logging
from collections import defaultdict, deque
from threading import Lock
from flask import request, jsonify

# Logger configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class RateLimiter:
    """
    Advanced rate limiting system with API abuse protection.
    Implements dynamic rate adjustment and anomaly detection.
    """
    def __init__(self, rate_limit: int, window_size: int, burst_limit: int = None, penalty_time: int = 300):
        """
        Initializes the rate limiter.

        Args:
            rate_limit (int): Maximum number of allowed requests in a given window.
            window_size (int): Time window in seconds for normal requests.
            burst_limit (int): Maximum burst requests allowed within a short period.
            penalty_time (int): Duration in seconds a client is banned if they exceed abuse thresholds.
        """
        self.rate_limit = rate_limit
        self.window_size = window_size
        self.burst_limit = burst_limit if burst_limit else rate_limit * 2  # Allow short bursts (default: 2x normal limit)
        self.penalty_time = penalty_time

        self.clients = defaultdict(deque)
        self.banned_clients = {}  # Stores banned clients with their ban expiration timestamp
        self.lock = Lock()

    def is_allowed(self, client_id: str) -> bool:
        """
        Determines if a client can make a request.

        Args:
            client_id (str): Unique client identifier (e.g., IP address).

        Returns:
            bool: True if the request is allowed, False if the limit is exceeded.
        """
        now = time.time()

        # Check if the client is currently banned
        if client_id in self.banned_clients and self.banned_clients[client_id] > now:
            logging.warning(f"⛔ Client {client_id} is temporarily banned until {self.banned_clients[client_id]}")
            return False
        elif client_id in self.banned_clients:
            del self.banned_clients[client_id]  # Remove expired bans

        with self.lock:
            request_times = self.clients[client_id]

            # Remove requests outside the time window
            while request_times and now - request_times[0] > self.window_size:
                request_times.popleft()

            # Enforce burst limit within a short time frame
            if len(request_times) > self.burst_limit:
                logging.warning(f"🚨 API Abuse Detected: {client_id} exceeded burst request limit.")
                self.banned_clients[client_id] = now + self.penalty_time  # Ban for penalty_time seconds
                self.clients[client_id].clear()
                return False

            # Enforce normal rate limit
            if len(request_times) < self.rate_limit:
                request_times.append(now)
                return True

        logging.warning(f"⚠️ Rate Limit Exceeded: {client_id} (Requests: {len(request_times)}/{self.rate_limit})")
        return False

    def get_remaining_requests(self, client_id: str) -> int:
        """
        Calculates the number of remaining requests for a client.

        Args:
            client_id (str): Unique client identifier.

        Returns:
            int: Number of remaining requests in the current window.
        """
        with self.lock:
            now = time.time()
            request_times = self.clients[client_id]
            self.clients[client_id] = deque([t for t in request_times if now - t <= self.window_size])
            return max(0, self.rate_limit - len(self.clients[client_id]))

    def get_penalty_time(self, client_id: str) -> int:
        """
        Checks if a client is banned and returns the remaining ban duration.

        Args:
            client_id (str): Unique client identifier.

        Returns:
            int: Seconds remaining in the penalty period.
        """
        now = time.time()
        return max(0, int(self.banned_clients.get(client_id, 0) - now))


# Middleware for Flask
class ThrottlingMiddleware:
    """
    Middleware to integrate the rate limiter with Flask, including abuse detection.
    """
    def __init__(self, app, rate_limit: int = 100, window_size: int = 60, burst_limit: int = None, penalty_time: int = 300):
        """
        Initializes the rate limiting middleware.

        Args:
            app: Flask application instance.
            rate_limit (int): Limit of requests per client.
            window_size (int): Duration of the time window in seconds.
            burst_limit (int): Maximum allowed burst requests.
            penalty_time (int): Ban duration for API abusers in seconds.
        """
        self.app = app
        self.rate_limiter = RateLimiter(rate_limit, window_size, burst_limit, penalty_time)
        self.app.before_request(self.check_rate_limit)

    def check_rate_limit(self):
        """
        Checks if a client has exceeded their request limit and responds accordingly.
        """
        client_id = request.remote_addr

        if client_id in self.rate_limiter.banned_clients:
            penalty_time = self.rate_limiter.get_penalty_time(client_id)
            response = jsonify({
                "error": "API abuse detected. You are temporarily banned.",
                "penalty_time_remaining": penalty_time
            })
            response.status_code = 403
            return response

        if not self.rate_limiter.is_allowed(client_id):
            remaining = self.rate_limiter.get_remaining_requests(client_id)
            response = jsonify({
                "error": "Rate limit exceeded",
                "remaining_requests": remaining,
                "reset_in_seconds": int(self.rate_limiter.window_size - (time.time() - min(self.rate_limiter.clients[client_id], default=0)))
            })
            response.status_code = 429
            return response


# Integration example
if __name__ == "__main__":
    from flask import Flask

    app = Flask(__name__)
    ThrottlingMiddleware(app, rate_limit=10, window_size=60, burst_limit=20, penalty_time=300)

    @app.route("/api/test")
    def test_endpoint():
        return jsonify({"message": "Request allowed!"})

    app.run(debug=True)
