import html
import re

def sanitize_input(data):
    """
    Sanitizes input data to prevent SQL injection and XSS attacks.

    Args:
        data (dict): The input data to sanitize.

    Returns:
        dict: The sanitized input data.
    """
    if isinstance(data, dict):
        sanitized_data = {}
        for key, value in data.items():
            if isinstance(value, dict):
                sanitized_data[key] = sanitize_input(value)
            elif isinstance(value, str):
                sanitized_data[key] = html.escape(re.sub(r"['\";]", "", value))  # Corrected regex pattern
            else:
                sanitized_data[key] = value
        return sanitized_data
    return data