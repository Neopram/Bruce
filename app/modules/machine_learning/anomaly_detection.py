import logging
import numpy as np
from sklearn.ensemble import IsolationForest
from app.modules.data_collector import DataCollector

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
ANOMALY_THRESHOLD = -0.5  # Isolation Forest threshold for anomaly detection
HISTORICAL_WINDOW = 100  # Number of recent order book snapshots to analyze

class MarketAnomalyDetector:
    """
    AI-driven anomaly detection system for market trend analysis.
    """

    def __init__(self, api_key: str, api_secret: str, passphrase: str):
        """
        Initializes the MarketAnomalyDetector with a real-time data collector.
        """
        self.collector = DataCollector(api_key, api_secret, passphrase)
        self.model = IsolationForest(contamination=0.05, random_state=42)
        self.data_history = []

    def extract_features(self, order_book):
        """
        Extracts relevant features from the order book data for anomaly detection.
        """
        if not order_book or "top_bid" not in order_book or "top_ask" not in order_book:
            return None
        spread = order_book.get("spread", 0)
        bid_price = float(order_book["top_bid"]["price"])
        ask_price = float(order_book["top_ask"]["price"])
        mid_price = (bid_price + ask_price) / 2
        return [mid_price, spread]

    def update_data_history(self, order_book):
        """
        Maintains a rolling window of historical order book data.
        """
        features = self.extract_features(order_book)
        if features:
            self.data_history.append(features)
        if len(self.data_history) > HISTORICAL_WINDOW:
            self.data_history.pop(0)

    def train_model(self):
        """
        Trains the Isolation Forest model on historical market data.
        """
        if len(self.data_history) < 10:
            logging.warning("⚠️ Insufficient data for training anomaly detection model.")
            return
        self.model.fit(np.array(self.data_history))
        logging.info("✅ Market anomaly detection model trained successfully.")

    def detect_anomalies(self, order_book):
        """
        Detects anomalies in the current market state.
        """
        features = self.extract_features(order_book)
        if not features or len(self.data_history) < 10:
            return False
        prediction = self.model.predict([features])[0]
        if prediction < ANOMALY_THRESHOLD:
            logging.warning("🚨 Market anomaly detected!")
            return True
        return False

    def analyze_market(self, instrument_id):
        """
        Continuously collects data and detects market anomalies.
        """
        logging.info("🚀 Market anomaly detection system running...")
        order_book = self.collector.fetch_and_process_order_book(instrument_id)
        self.update_data_history(order_book)
        self.train_model()
        if self.detect_anomalies(order_book):
            logging.error("⚠️ Possible market manipulation detected!")
        else:
            logging.info("✅ Market conditions are normal.")

if __name__ == "__main__":
    API_KEY = "your_api_key"
    API_SECRET = "your_api_secret"
    PASSPHRASE = "your_passphrase"
    detector = MarketAnomalyDetector(API_KEY, API_SECRET, PASSPHRASE)
    detector.analyze_market("BTC-USDT")
