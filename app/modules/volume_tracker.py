import logging
import requests
from collections import deque
from statistics import mean
from app.modules.alert_system import AlertSystem
from app.config.settings import Config

# Logger configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class VolumeTracker:
    """
    Monitors trading volume trends and detects abnormal activity.
    """

    def __init__(self, window_size: int = 10):
        """
        Initializes the volume tracker.

        Args:
            window_size (int): Number of recent volumes to consider for analysis.
        """
        self.window_size = window_size
        self.volume_window = deque(maxlen=window_size)

    def update_volume(self, new_volume: float):
        """
        Updates the tracker with the latest trading volume.

        Args:
            new_volume (float): The latest volume data.
        """
        self.volume_window.append(new_volume)
        logging.info(f"Updated volume window: {list(self.volume_window)}")

    def calculate_average_volume(self) -> float:
        """
        Calculates the average trading volume over the window.

        Returns:
            float: The average trading volume.
        """
        if not self.volume_window:
            logging.warning("Volume window is empty. Returning 0.")
            return 0.0
        avg_volume = mean(self.volume_window)
        logging.info(f"Average volume: {avg_volume}")
        return avg_volume

    def detect_spike(self, threshold: float) -> bool:
        """
        Detects if there is a significant spike in trading volume.

        Args:
            threshold (float): The multiplier threshold for spike detection.

        Returns:
            bool: True if a spike is detected, False otherwise.
        """
        if len(self.volume_window) < self.window_size:
            logging.warning("Insufficient data to detect spikes.")
            return False

        avg_volume = self.calculate_average_volume()
        latest_volume = self.volume_window[-1]

        if latest_volume > avg_volume * threshold:
            logging.info(f"Spike detected! Latest volume: {latest_volume}, Threshold: {avg_volume * threshold}")
            return True

        logging.info("No spike detected.")
        return False

    def fetch_current_volume(self):
        """
        Retrieves real-time trading volume from OKX.

        Returns:
            float: Latest trading volume.
        """
        endpoint = f"https://www.okx.com/api/v5/market/ticker?instId={Config.TRADING_PAIR.replace('/', '-')}"
        try:
            response = requests.get(endpoint)
            response.raise_for_status()
            data = response.json()
            volume = float(data["data"][0]["volUsd"])
            logging.info(f"Retrieved OKX volume: {volume}")
            return volume
        except Exception as e:
            logging.error(f"Error fetching volume from OKX: {e}")
            return None


class VolumeAlertSystem:
    """
    Integrated alert system for detecting and reporting volume spikes.
    """

    def __init__(self, alert_system: AlertSystem, window_size: int = 10, threshold: float = 2.0):
        """
        Initializes the volume alert system.

        Args:
            alert_system (AlertSystem): The alert system instance.
            window_size (int): Number of volumes to track.
            threshold (float): Multiplier threshold for spike detection.
        """
        self.volume_tracker = VolumeTracker(window_size=window_size)
        self.alert_system = alert_system
        self.threshold = threshold

    def process_volume(self):
        """
        Fetches the latest volume from OKX, processes it, and checks for spikes.
        """
        latest_volume = self.volume_tracker.fetch_current_volume()
        if latest_volume is not None:
            self.volume_tracker.update_volume(latest_volume)
            if self.volume_tracker.detect_spike(self.threshold):
                self.alert_system.send_alert(
                    f"Volume spike detected! Latest volume: {latest_volume}"
                )


# Example usage
if __name__ == "__main__":
    alert_system = AlertSystem(
        recipients=["admin@example.com"],
        smtp_server="smtp.example.com",
        smtp_port=587,
        smtp_user="user@example.com",
        smtp_password="password",
    )

    volume_alert = VolumeAlertSystem(alert_system, window_size=10, threshold=2.0)

    # Fetch and process real-time volume
    volume_alert.process_volume()
