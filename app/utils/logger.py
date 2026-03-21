import logging
import os
import json
import time
import psutil
import functools
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Dict, Any, Callable

# Directory for logs
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, "bot_activity.log")


class StructuredLogger:
    """
    Advanced structured logging system with error tracing, performance analytics, and integration support.
    Includes execution time tracking, memory usage monitoring, and structured JSON logging.
    """

    def __init__(self, log_file=LOG_FILE, max_bytes=10 * 1024 * 1024, backup_count=5):
        """
        Initializes structured logging with rotation, JSON formatting, and advanced analytics.

        Args:
            log_file (str): Path to the log file.
            max_bytes (int): Maximum log file size before rotation.
            backup_count (int): Number of backup log files to keep.
        """
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        self.logger = logging.getLogger("StructuredLogger")
        self.logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - Line %(lineno)d - %(message)s"
        )

        file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def log(self, level: str, message: str, extra: Dict[str, Any] = None):
        """
        Logs a structured message in JSON format.

        Args:
            level (str): Logging level ('INFO', 'WARNING', 'ERROR', 'DEBUG', 'CRITICAL').
            message (str): Log message.
            extra (Dict[str, Any], optional): Additional metadata for structured logging.
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "metadata": extra or {}
        }
        self.logger.log(getattr(logging, level.upper(), logging.INFO), json.dumps(log_data))

    def info(self, message: str, **kwargs):
        """Logs an INFO level message."""
        self.log("INFO", message, kwargs)

    def warning(self, message: str, **kwargs):
        """Logs a WARNING level message."""
        self.log("WARNING", message, kwargs)

    def error(self, message: str, **kwargs):
        """Logs an ERROR level message."""
        self.log("ERROR", message, kwargs)

    def debug(self, message: str, **kwargs):
        """Logs a DEBUG level message."""
        self.log("DEBUG", message, kwargs)

    def log_trade(self, trade_data: Dict[str, Any]):
        """
        Logs trade execution details.

        Args:
            trade_data (Dict[str, Any]): Trade execution details.
        """
        self.info("Trade executed", **trade_data)

    def log_error(self, error_msg: str, error_details: Dict[str, Any] = None):
        """
        Logs error messages with stack trace details.

        Args:
            error_msg (str): Description of the error.
            error_details (Dict[str, Any], optional): Additional details (e.g., API response, function name).
        """
        self.error(error_msg, **(error_details or {}))

    def trace_execution_time(self, func: Callable) -> Callable:
        """
        Decorator to measure execution time of a function.

        Args:
            func (Callable): Function to measure.

        Returns:
            Callable: Wrapped function with execution time logging.
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            self.info(f"Execution time for {func.__name__}", execution_time=f"{execution_time:.4f} seconds")
            return result
        return wrapper

    def track_memory_usage(self) -> float:
        """
        Tracks and logs the memory usage of the current process.

        Returns:
            float: The memory usage in MB.
        """
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_usage = memory_info.rss / (1024 ** 2)  # Convert to MB
        self.info("Memory usage recorded", memory_usage_mb=round(memory_usage, 2))
        return memory_usage

    def get_system_metrics(self) -> Dict[str, float]:
        """
        Retrieves and logs system metrics such as CPU usage, memory usage, and disk usage.

        Returns:
            Dict[str, float]: A dictionary with system metrics.
        """
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        disk_usage = psutil.disk_usage('/')

        metrics = {
            "cpu_usage_percent": cpu_usage,
            "memory_usage_percent": memory_info.percent,
            "disk_usage_percent": disk_usage.percent,
            "available_memory_mb": memory_info.available / (1024 ** 2),
        }
        self.info("System Metrics Recorded", **metrics)
        return metrics

    def monitor_function(self, func: Callable) -> Callable:
        """
        Decorator to monitor both execution time and memory usage of a function.

        Args:
            func (Callable): The function to be monitored.

        Returns:
            Callable: The wrapped function with monitoring.
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            process = psutil.Process()
            memory_before = process.memory_info().rss
            result = func(*args, **kwargs)
            memory_after = process.memory_info().rss
            end_time = time.time()
            execution_time = end_time - start_time
            memory_usage = (memory_after - memory_before) / (1024 ** 2)  # Convert to MB
            self.info(f"Execution time for {func.__name__}", execution_time=f"{execution_time:.2f} seconds")
            self.info(f"Memory usage for {func.__name__}", memory_usage_mb=f"{memory_usage:.2f} MB")
            return result
        return wrapper


# Example usage
if __name__ == "__main__":
    logger = StructuredLogger()

    @logger.trace_execution_time
    def sample_function():
        time.sleep(1)  # Simulating a process
        logger.info("Sample function executed successfully")

    sample_function()

    # Example trade log
    trade_example = {
        "pair": "USDT/AED",
        "order_type": "LIMIT",
        "side": "BUY",
        "amount": 1000,
        "price": 3.67,
        "status": "FILLED"
    }
    logger.log_trade(trade_example)

    # Example error log
    try:
        1 / 0  # Intentional error
    except ZeroDivisionError as e:
        logger.log_error("Math error", {"exception": str(e)})

    # Example system metrics logging
    logger.get_system_metrics()
