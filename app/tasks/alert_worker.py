import logging
import time
from threading import Thread
from queue import PriorityQueue
from app.modules.alert_system import AlertSystem

# Logger configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class AlertWorker:
    """
    Worker responsible for processing and dispatching alerts with priority-based handling.
    Alerts are scored based on risk level and processed accordingly.
    """

    def __init__(self, alert_system: AlertSystem, polling_interval: int = 5):
        """
        Initializes the AlertWorker.

        Args:
            alert_system (AlertSystem): Instance of the alert system for sending notifications.
            polling_interval (int): Interval in seconds for polling alerts.
        """
        self.alert_system = alert_system
        self.alert_queue = PriorityQueue()  # Priority queue to process high-risk alerts first
        self.polling_interval = polling_interval
        self.running = False
        self.alert_cooldown = {}  # To prevent spam alerts

    def start(self):
        """
        Starts the alert worker in a separate thread.
        """
        self.running = True
        worker_thread = Thread(target=self._process_alerts, daemon=True)
        worker_thread.start()
        logging.info("✅ AlertWorker started and running in background.")

    def stop(self):
        """
        Stops the alert worker gracefully.
        """
        self.running = False
        logging.info("⛔ AlertWorker stopped.")

    def enqueue_alert(self, message: str, recipients: list, risk_level: int = 1):
        """
        Enqueues an alert for processing, assigning a priority based on risk level.
        
        Priority levels:
        - 1: Low priority (General notifications)
        - 2: Medium priority (Market changes)
        - 3: High priority (Critical market anomalies, liquidation warnings)
        - 4: Urgent (Security breaches, API failures)

        Args:
            message (str): The alert message to be sent.
            recipients (list): List of recipients for the alert.
            risk_level (int): Priority level (higher means more urgent).
        """
        timestamp = time.time()

        # Avoid spam: Ignore duplicate alerts within 60 seconds
        if message in self.alert_cooldown and timestamp - self.alert_cooldown[message] < 60:
            logging.info(f"⏳ Alert skipped (recently sent): {message}")
            return

        self.alert_cooldown[message] = timestamp
        self.alert_queue.put((-risk_level, message, recipients))  # Negative priority for highest first
        logging.info(f"📌 Alert enqueued: [{risk_level}] {message}")

    def _process_alerts(self):
        """
        Internal method for processing alerts from the queue.
        """
        while self.running:
            try:
                if not self.alert_queue.empty():
                    priority, message, recipients = self.alert_queue.get()
                    logging.info(f"🚀 Processing Alert: {message} (Priority {abs(priority)})")

                    # Send alerts based on priority
                    if abs(priority) >= 3:
                        self.alert_system.send_alert(message, alert_type="all")  # High priority → All channels
                    elif abs(priority) == 2:
                        self.alert_system.send_alert(message, alert_type="telegram")  # Medium priority → Telegram
                    else:
                        self.alert_system.send_alert(message, alert_type="email")  # Low priority → Email only

                    logging.info(f"✅ Alert dispatched successfully: {message}")

                else:
                    time.sleep(self.polling_interval)
            except Exception as e:
                logging.error(f"❌ Error processing alert: {e}")


# Example usage
if __name__ == "__main__":
    alert_system = AlertSystem(
        recipients=["user@example.com"],
        smtp_config={
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "smtp_user": "your_email@example.com",
            "smtp_password": "your_password"
        },
        telegram_config={
            "bot_token": "your_telegram_bot_token",
            "chat_id": "your_chat_id"
        },
        discord_webhook="your_discord_webhook_url"
    )

    alert_worker = AlertWorker(alert_system)
    alert_worker.start()

    # Test alerts
    alert_worker.enqueue_alert("⚠️ Market dip detected! Price dropped 5% in 5 minutes.", ["user@example.com"], risk_level=2)
    alert_worker.enqueue_alert("🚨 Liquidation warning! Your position is at risk!", ["user@example.com"], risk_level=4)

    time.sleep(10)
    alert_worker.stop()
