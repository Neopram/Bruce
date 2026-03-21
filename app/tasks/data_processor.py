import logging
import time
from threading import Thread
from queue import Queue
from app.modules.data_collector import DataCollector
from app.modules.data_transformer import DataTransformer
from app.modules.alert_system import AlertSystem

# Logger configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class DataProcessor:
    """
    Worker responsible for processing and transforming data in real-time and batch mode.
    """
    def __init__(self, data_collector: DataCollector, alert_system: AlertSystem, polling_interval: int = 5):
        """
        Initializes the DataProcessor.

        Args:
            data_collector (DataCollector): Instance of the data collector for fetching raw data.
            alert_system (AlertSystem): Instance of the alert system for notifications.
            polling_interval (int): Interval in seconds for polling new data.
        """
        self.data_collector = data_collector
        self.data_transformer = DataTransformer()
        self.alert_system = alert_system
        self.data_queue = Queue()
        self.polling_interval = polling_interval
        self.running = False

    def start(self):
        """
        Starts the data processor in a separate thread.
        """
        self.running = True
        collector_thread = Thread(target=self._collect_data, daemon=True)
        processor_thread = Thread(target=self._process_data, daemon=True)
        collector_thread.start()
        processor_thread.start()
        logging.info("DataProcessor started.")

    def stop(self):
        """
        Stops the data processor gracefully.
        """
        self.running = False
        logging.info("DataProcessor stopped.")

    def _collect_data(self):
        """
        Collects raw data and enqueues it for processing.
        """
        while self.running:
            try:
                raw_data = self.data_collector.fetch_data()
                if raw_data:
                    self.data_queue.put(raw_data)
                    logging.info(f"Raw data enqueued: {raw_data}")
                time.sleep(self.polling_interval)
            except Exception as e:
                logging.error(f"Error collecting data: {e}")
                self.alert_system.send_alert(f"Data collection error: {e}", recipients=["admin@example.com"])

    def _process_data(self):
        """
        Processes data from the queue and applies transformations.
        """
        while self.running:
            try:
                if not self.data_queue.empty():
                    raw_data = self.data_queue.get()
                    processed_data = self.data_transformer.transform(raw_data)
                    logging.info(f"Processed data: {processed_data}")
                    # Here you can forward the processed data to other systems or save it.
                else:
                    time.sleep(self.polling_interval)
            except Exception as e:
                logging.error(f"Error processing data: {e}")
                self.alert_system.send_alert(f"Data processing error: {e}", recipients=["admin@example.com"])
