import pandas as pd
import logging
from datetime import datetime
from typing import Dict, Any, Union

# Logger configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class DataTransformer:
    """
    Module responsible for transforming raw market data into structured and usable formats.
    """

    def __init__(self):
        """
        Initializes the DataTransformer.
        """
        logging.info("DataTransformer initialized.")

    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Union[str, float]]:
        """
        Transforms raw data into a structured format.

        Args:
            raw_data (dict): Raw data dictionary with keys like "price", "volume", "timestamp".

        Returns:
            dict: Transformed data with validated and processed fields.
        """
        try:
            if not self._validate_raw_data(raw_data):
                raise ValueError("Invalid raw data format.")

            # Convert timestamp to a readable format
            transformed_data = {
                "timestamp": self._convert_timestamp(raw_data["timestamp"]),
                "price": self._convert_to_float(raw_data["price"]),
                "volume": self._convert_to_float(raw_data["volume"]),
                "source": raw_data.get("source", "unknown"),  # Adds source tracking
                "currency_pair": raw_data.get("currency_pair", "N/A")  # Tracks trading pair
            }

            logging.info(f"Data transformed successfully: {transformed_data}")
            return transformed_data
        except Exception as e:
            logging.error(f"Error transforming data: {e}")
            raise

    def _validate_raw_data(self, raw_data: Dict[str, Any]) -> bool:
        """
        Validates the structure and content of raw data.

        Args:
            raw_data (dict): Raw data dictionary.

        Returns:
            bool: True if data is valid, False otherwise.
        """
        required_keys = {"price", "volume", "timestamp"}
        if not required_keys.issubset(raw_data.keys()):
            logging.warning(f"Missing required keys in raw data: {raw_data}")
            return False

        for key in required_keys:
            if not isinstance(raw_data[key], (int, float, str)):
                logging.warning(f"Invalid type for key {key} in raw data: {raw_data}")
                return False

        return True

    def _convert_timestamp(self, timestamp: Union[str, int]) -> str:
        """
        Converts a UNIX timestamp to ISO 8601 format.

        Args:
            timestamp (str or int): UNIX timestamp.

        Returns:
            str: ISO 8601 formatted timestamp.
        """
        try:
            dt_object = datetime.utcfromtimestamp(int(timestamp))
            return dt_object.isoformat()
        except Exception as e:
            logging.error(f"Error converting timestamp: {e}")
            raise

    def _convert_to_float(self, value: Union[str, float, int]) -> float:
        """
        Converts a value to float safely.

        Args:
            value (str, float, int): Numeric value.

        Returns:
            float: Converted float value.
        """
        try:
            return float(value)
        except ValueError as e:
            logging.error(f"Error converting value to float: {value}, {e}")
            raise


if __name__ == "__main__":
    # Example usage
    raw_data_example = {
        "price": "102.5",
        "volume": "200",
        "timestamp": "1679606203",
        "source": "Binance",
        "currency_pair": "BTC/USDT"
    }

    transformer = DataTransformer()
    transformed_data = transformer.transform(raw_data_example)
    print(transformed_data)
