import logging
import json
import time
import websocket
import threading
import random
from queue import Queue
from flask_socketio import SocketIO, emit
from flask import request
from app.config.settings import Config
from app.modules.alert_system import AlertSystem

# Logger configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize global WebSocket event queue
event_queue = Queue()

# WebSocket Configuration
MAX_RECONNECT_ATTEMPTS = 10
BASE_RECONNECT_DELAY = 3  # in seconds
JITTER_FACTOR = 0.5  # Adds randomness to avoid synchronized reconnects


class WebSocketManager:
    """
    Manages WebSocket connections and real-time notifications.
    """

    def __init__(self, app=None):
        """
        Initializes the WebSocket manager.

        Args:
            app: Flask application instance (optional during initialization).
        """
        self.socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")
        self.ws = None
        self.reconnect_attempts = 0
        self.okx_websocket_url = Config.OKX_WEBSOCKET_URI
        self.subscribed_channels = [
            {
                "channel": "books",
                "instId": Config.TRADING_PAIR.replace("/", "-")  # Format required by OKX
            }
        ]
        self.alert_system = AlertSystem(
            telegram_config={"bot_token": Config.TELEGRAM_BOT_TOKEN, "chat_id": Config.TELEGRAM_CHAT_ID},
            discord_webhook=Config.DISCORD_WEBHOOK_URL
        )

    def initialize(self, app):
        """
        Binds the WebSocket to the Flask application.

        Args:
            app: Flask application instance.
        """
        self.socketio.init_app(app)

    def broadcast_message(self, event: str, data: dict):
        """
        Sends a message to all connected clients.

        Args:
            event (str): Event name.
            data (dict): Data to send.
        """
        logging.info(f"Broadcasting event: {event}")
        self.socketio.emit(event, data, broadcast=True)

    def connect_to_okx(self):
        """
        Establishes connection to the OKX WebSocket API.
        """
        logging.info("Attempting to connect to OKX WebSocket...")

        def on_message(ws, message):
            """
            Handles incoming messages from OKX WebSocket.

            Args:
                ws: WebSocket instance.
                message: JSON message received.
            """
            data = json.loads(message)
            if "data" in data:
                event_queue.put(data)  # Push data to the event queue
                self.broadcast_message("order_book_update", data)

        def on_error(ws, error):
            """
            Handles WebSocket errors.

            Args:
                ws: WebSocket instance.
                error: Error message.
            """
            logging.error(f"WebSocket error: {error}")
            self.alert_system.send_alert(f"WebSocket error: {error}", alert_type="telegram")
            self.reconnect()

        def on_close(ws, close_status_code, close_msg):
            """
            Handles WebSocket closure events.

            Args:
                ws: WebSocket instance.
                close_status_code: Status code of closure.
                close_msg: Closure message.
            """
            logging.warning(f"WebSocket closed: {close_status_code} - {close_msg}")
            self.reconnect()

        def on_open(ws):
            """
            Handles WebSocket connection opening and subscribes to order book updates.
            """
            logging.info("WebSocket connection established. Subscribing to channels...")
            subscription_message = {
                "op": "subscribe",
                "args": self.subscribed_channels
            }
            ws.send(json.dumps(subscription_message))

        # Start WebSocket connection
        self.ws = websocket.WebSocketApp(
            self.okx_websocket_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        self.ws.on_open = on_open

        thread = threading.Thread(target=self.ws.run_forever)
        thread.daemon = True
        thread.start()

    def reconnect(self):
        """
        Attempts to reconnect to OKX WebSocket if disconnected.
        """
        if self.reconnect_attempts < MAX_RECONNECT_ATTEMPTS:
            self.reconnect_attempts += 1
            delay = BASE_RECONNECT_DELAY * (2 ** self.reconnect_attempts) + random.uniform(0, JITTER_FACTOR)
            logging.info(f"Reconnecting in {round(delay, 2)} seconds... Attempt {self.reconnect_attempts}/{MAX_RECONNECT_ATTEMPTS}")
            time.sleep(delay)
            self.connect_to_okx()
        else:
            logging.error("Max reconnection attempts reached. WebSocket will not reconnect automatically.")
            self.alert_system.send_alert("WebSocket max reconnection attempts reached!", alert_type="telegram")

    def process_event_queue(self):
        """
        Processes messages from the event queue asynchronously.
        """
        while True:
            if not event_queue.empty():
                event_data = event_queue.get()
                self.broadcast_message("order_book_update", event_data)
            time.sleep(0.1)  # Prevent CPU overutilization

    def run_socketio(self, host="0.0.0.0", port=5000):
        """
        Runs the WebSocket server.

        Args:
            host (str): Host address.
            port (int): Port to listen for connections.
        """
        logging.info(f"Starting WebSocket server on {host}:{port}")
        threading.Thread(target=self.process_event_queue, daemon=True).start()
        self.socketio.run(app=request.app, host=host, port=port)


# Registering WebSocket events
socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")


@socketio.on("connect")
def handle_connect():
    """
    Handles new client connections.
    """
    logging.info(f"Client connected from {request.remote_addr}")
    emit("connection_response", {"status": "connected"})


@socketio.on("disconnect")
def handle_disconnect():
    """
    Handles client disconnections.
    """
    logging.info(f"Client disconnected from {request.remote_addr}")


@socketio.on("custom_event")
def handle_custom_event(data):
    """
    Handles custom events sent by clients.

    Args:
        data (dict): Data received from the client.
    """
    logging.info(f"Custom event received: {data}")
    emit("custom_event_response", {"response": "Event received successfully"})


# Start WebSocket connection to OKX when the module is loaded
websocket_manager = WebSocketManager()
websocket_manager.connect_to_okx()
