import schedule
import time
import logging
from workers.alert_worker import AlertWorker
from workers.data_processor import DataProcessor
from workers.retraining_worker import RetrainingWorker

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class TaskScheduler:
    """
    Schedules and manages automated tasks for the trading bot.
    """

    def __init__(self):
        """
        Initializes the TaskScheduler and its associated workers.
        """
        self.alert_worker = AlertWorker()
        self.data_processor = DataProcessor()
        self.retraining_worker = RetrainingWorker()

    def schedule_tasks(self):
        """
        Schedules periodic tasks using the schedule library.
        """
        # Task: Process incoming data
        schedule.every(5).minutes.do(self.data_processor.process_data)

        # Task: Run alert checks
        schedule.every(1).minute.do(self.alert_worker.check_and_dispatch_alerts)

        # Task: Retrain models
        schedule.every().day.at("03:00").do(self.retraining_worker.retrain_models)

        logging.info("All tasks scheduled successfully.")

    def run_scheduler(self):
        """
        Runs the task scheduler indefinitely.
        """
        self.schedule_tasks()
        logging.info("Starting the task scheduler...")

        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                logging.info("Task scheduler stopped.")
                break
            except Exception as e:
                logging.error(f"An error occurred in the task scheduler: {e}")


# Entry point for the task scheduler
if __name__ == "__main__":
    task_scheduler = TaskScheduler()
    task_scheduler.run_scheduler()
