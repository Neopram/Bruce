import logging
import json
import os
import time
import psutil
import functools
from logging.handlers import RotatingFileHandler
from typing import Dict, Callable, Any

# Directory for logs
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, "bot_activity.log")


class StructuredLogger:
    """
    Advanced structured logging system with error tracing, performance analytics,
    and system diagnostics.
    """

    def __init__(self, log_file=LOG_FILE, max_bytes=10 * 1024 * 1024, backup_count=5):
        """
        Initializes structured logging with rotation, JSON formatting, and performance tracking.

        Args:
            log_file (str): Path to the log file.
            max_bytes (int): Maximum log file size before rotation.
            backup_count (int): Number of backup log files to keep.
        """
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        self.logger = logging.getLogger("TradingBotLogger")
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
        Logs a structured message.

        Args:
            level (str): Log level ('INFO', 'WARNING', 'ERROR', 'DEBUG', 'CRITICAL').
            message (str): Log message.
            extra (Dict[str, Any], optional): Additional metadata for structured logging.
        """
        log_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "level": level,
            "message": message,
        }

        if extra:
            log_data.update(extra)

        log_message = json.dumps(log_data)

        if level == "INFO":
            self.logger.info(log_message)
        elif level == "WARNING":
            self.logger.warning(log_message)
        elif level == "ERROR":
            self.logger.error(log_message)
        elif level == "DEBUG":
            self.logger.debug(log_message)
        elif level == "CRITICAL":
            self.logger.critical(log_message)

    def log_trade(self, trade_data: Dict[str, Any]):
        """
        Logs trade execution details.

        Args:
            trade_data (Dict[str, Any]): Trade execution details.
        """
        self.log("INFO", "Trade executed", trade_data)

    def log_error(self, error_msg: str, error_details: Dict[str, Any] = None):
        """
        Logs error messages with stack trace details.

        Args:
            error_msg (str): Description of the error.
            error_details (Dict[str, Any], optional): Additional details (e.g., API response, function name).
        """
        self.log("ERROR", error_msg, error_details)

    def log_performance(self, function_name: str, execution_time: float, memory_usage: float = None):
        """
        Logs execution time and memory usage of a function.

        Args:
            function_name (str): Name of the function being monitored.
            execution_time (float): Time taken for execution in seconds.
            memory_usage (float, optional): Memory used by the function in MB.
        """
        performance_data = {
            "function": function_name,
            "execution_time_sec": round(execution_time, 4),
        }
        if memory_usage:
            performance_data["memory_usage_mb"] = round(memory_usage, 2)

        self.log("DEBUG", "Performance Metrics", performance_data)

    def track_execution_time(self, func: Callable) -> Callable:
        """
        Decorator to measure the execution time of a function.

        Args:
            func (Callable): The function to measure.

        Returns:
            Callable: The wrapped function with execution time logging.
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            elapsed_time = end_time - start_time
            self.log("INFO", f"Execution time for {func.__name__}: {elapsed_time:.4f} seconds.")
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
        self.log("INFO", f"Memory usage: {memory_usage:.2f} MB")
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
            "cpu_usage": cpu_usage,
            "memory_usage": memory_info.percent,
            "disk_usage": disk_usage.percent,
            "available_memory_mb": memory_info.available / (1024 ** 2),
        }
        self.log("INFO", "System Metrics", metrics)
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
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            process = psutil.Process()
            memory_before = process.memory_info().rss
            result = func(*args, **kwargs)
            memory_after = process.memory_info().rss
            end_time = time.time()
            execution_time = end_time - start_time
            memory_usage = (memory_after - memory_before) / (1024 ** 2)  # Convert to MB
            self.log("INFO", f"Execution time for {func.__name__}: {execution_time:.2f} seconds")
            self.log("INFO", f"Memory usage for {func.__name__}: {memory_usage:.2f} MB")
            return result
        return wrapper


# Example usage
if __name__ == "__main__":
    logger = StructuredLogger()

    @logger.track_execution_time
    def sample_task():
        time.sleep(2)
        return "Task Completed"

    # Run sample task with monitoring
    result = sample_task()
    print(result)

    # Monitor system resource usage
    system_metrics = logger.get_system_metrics()
    print("Monitored Metrics:", system_metrics)
