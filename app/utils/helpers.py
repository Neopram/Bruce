from datetime import datetime
import re
import time
from functools import wraps

def calculate_percentage_change(previous: float, current: float) -> float:
    """
    Calculates the percentage change between two values.

    Args:
        previous (float): The previous value.
        current (float): The current value.

    Returns:
        float: The percentage change.
    """
    if previous == 0:
        raise ValueError("Previous value cannot be zero when calculating percentage change.")
    return ((current - previous) / previous) * 100

def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Formats a datetime object into a string.

    Args:
        dt (datetime): The datetime object to format.
        fmt (str): The format string. Defaults to '%Y-%m-%d %H:%M:%S'.

    Returns:
        str: The formatted datetime string.
    """
    return dt.strftime(fmt)

def is_valid_email(email: str) -> bool:
    """
    Validates if the provided string is a valid email address.

    Args:
        email (str): The email address to validate.

    Returns:
        bool: True if the email is valid, False otherwise.
    """
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

def retry_on_exception(retries: int = 3, delay: int = 2, exception: Exception = Exception):
    """
    Decorator to retry a function if a specific exception is raised.

    Args:
        retries (int): Number of retry attempts.
        delay (int): Delay in seconds between retries.
        exception (Exception): Exception type to catch for retries.

    Returns:
        Callable: Decorated function with retry logic.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except exception as e:
                    if attempt < retries - 1:
                        time.sleep(delay)
                    else:
                        raise
        return wrapper
    return decorator