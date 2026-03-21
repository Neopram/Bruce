import json
import logging
import asyncio
import pandas as pd
from collections import deque
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime
from typing import Dict, Any
from app.utils.database import DatabaseManager  # Optional: Enables storing snapshots

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class DataHandler:
    """
    Handles real-time market data transformation, validation, and storage.
    """

    def __init__(self, buffer_size: int = 500, enable_db_storage: bool = False):
        """
        Initializes the real-time data handler.

        Args:
            buffer_size (int): Max number of data points to store in memory.
            enable_db_storage (bool): Whether to persist data in a database.
        """
        self.buffer_size = buffer_size
        self.data_buffer = deque(maxlen=buffer_size)
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.enable_db_storage = enable_db_storage

        if self.enable_db_storage:
            self.db_manager = DatabaseManager()

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validates incoming market data.

        Args:
            data (Dict[str, Any]): JSON-like data.

        Returns:
            bool: True if valid, False otherwise.
        """
        required_keys = {"exchange", "price", "volume", "timestamp"}

        if not required_keys.issubset(data.keys()):
            logging.warning(f"⚠️ Missing required keys in data: {data}")
            return False

        # Ensure valid data types
        try:
            float(data["price"])
            float(data["volume"])
            datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S")
        except (ValueError, KeyError):
            logging.error(f"❌ Invalid data format: {data}")
            return False

        return True

    def transform_data(self, data: Dict[str, Any]) -> pd.DataFrame:
        """
        Transforms incoming data into a structured DataFrame.

        Args:
            data (Dict[str, Any]): Market data.

        Returns:
            pd.DataFrame: Normalized, structured data.
        """
        df = pd.DataFrame([data])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df[["exchange", "timestamp", "price", "volume"]]

        # Normalize price and volume
        df[["price", "volume"]] = self.scaler.fit_transform(df[["price", "volume"]])

        logging.info(f"🔄 Transformed Data: {df.to_dict(orient='records')}")
        return df

    async def store_data(self, data: Dict[str, Any]):
        """
        Validates, transforms, and stores data.

        Args:
            data (Dict[str, Any]): Market data.
        """
        if not self.validate_data(data):
            return

        transformed_data = self.transform_data(data)

        # Store in memory buffer
        self.data_buffer.append(transformed_data)

        # Optional: Store in database for historical tracking
        if self.enable_db_storage:
            await self.db_manager.insert_trade({
                "trading_pair": "BTC/USDT",  # Can be extracted dynamically
                "action": "BUY" if data["volume"] > 0 else "SELL",
                "price": data["price"],
                "volume": data["volume"],
                "timestamp": data["timestamp"],
            })

        logging.info(f"✅ Data stored. Buffer size: {len(self.data_buffer)}")

    def get_latest_data(self) -> pd.DataFrame:
        """
        Retrieves the latest market data.

        Returns:
            pd.DataFrame: Most recent stored data.
        """
        return pd.concat(self.data_buffer, ignore_index=True) if self.data_buffer else pd.DataFrame()


# Example Usage
if __name__ == "__main__":
    handler = DataHandler(buffer_size=500, enable_db_storage=True)

    # Simulated market data
    sample_data = {
        "exchange": "Binance",
        "price": 45200.50,
        "volume": 1.2,
        "timestamp": "2025-02-20 14:35:00"
    }

    asyncio.run(handler.store_data(sample_data))

    # Retrieve stored data
    latest_data = handler.get_latest_data()
    print("📊 Latest Data:", latest_data)
