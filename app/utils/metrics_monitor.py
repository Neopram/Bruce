import time
import psutil
import functools
import logging
from typing import Dict, Callable

class MonitoringTools:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def track_execution_time(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            self.logger.info(f"Execution time for {func.__name__}: {execution_time:.2f} seconds")
            return execution_time
        return wrapper

    def track_memory_usage(self) -> float:
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_usage = memory_info.rss / (1024 ** 2)  # Convert to MB
        self.logger.info(f"Memory usage: {memory_usage:.2f} MB")
        return memory_usage

    def get_system_metrics(self) -> Dict[str, float]:
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        disk_usage = psutil.disk_usage('/')
        metrics = {
            "cpu_usage": cpu_usage,
            "memory_usage": memory_info.percent,
            "disk_usage": disk_usage.percent,
            "available_memory_mb": memory_info.available / (1024 ** 2),
        }
        self.logger.info(f"System Metrics: {metrics}")
        return metrics

    @staticmethod
    def monitor_resource_usage() -> Dict[str, float]:
        """
        Monitors and returns system resource usage (e.g., CPU and memory).

        Returns:
            Dict[str, float]: A dictionary with CPU and memory usage.
        """
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            metrics = {
                "CPU Usage (%)": cpu_usage,
                "Memory Usage (%)": memory_info.percent,
                "Available Memory (MB)": memory_info.available / (1024 * 1024),
            }
            MonitoringTools.log_system_metrics(metrics)
            return metrics
        except Exception as e:
            logging.error(f"Error monitoring resource usage: {e}")
            return {}

    @staticmethod
    def log_system_metrics(metrics: Dict[str, float]):
        """
        Logs system metrics.

        Args:
            metrics (Dict[str, float]): A dictionary with system metrics.
        """
        logging.info(f"System Metrics: {metrics}")

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
            self.logger.info(f"Execution time for {func.__name__}: {execution_time:.2f} seconds")
            self.logger.info(f"Memory usage for {func.__name__}: {memory_usage:.2f} MB")
            return result
        return wrapper