# Utilities and shared helpers for symbolic backend

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


# ─── Timestamp Helpers ───────────────────────────────────────────────

def utc_now() -> str:
    """Return current UTC timestamp as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def utc_now_dt() -> datetime:
    """Return current UTC datetime object."""
    return datetime.now(timezone.utc)


def timestamp_ms() -> int:
    """Return current UTC timestamp in milliseconds."""
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def parse_iso(iso_str: str) -> datetime:
    """Parse an ISO 8601 string into a datetime object."""
    return datetime.fromisoformat(iso_str)


# ─── Response Formatters ─────────────────────────────────────────────

class BruceResponse(BaseModel):
    """Standard response envelope for Bruce API endpoints."""
    success: bool = True
    timestamp: str = ""
    data: Any = None
    message: str = ""
    error: Optional[str] = None

    def __init__(self, **kwargs):
        if "timestamp" not in kwargs or not kwargs["timestamp"]:
            kwargs["timestamp"] = utc_now()
        super().__init__(**kwargs)


def success_response(data: Any = None, message: str = "OK") -> Dict[str, Any]:
    """Build a standard success response dict."""
    return {
        "success": True,
        "timestamp": utc_now(),
        "data": data,
        "message": message,
    }


def error_response(message: str, detail: Optional[str] = None, code: int = 400) -> Dict[str, Any]:
    """Build a standard error response dict."""
    return {
        "success": False,
        "timestamp": utc_now(),
        "error": message,
        "detail": detail,
        "code": code,
    }


def paginated_response(
    items: List[Any],
    total: int,
    page: int = 1,
    page_size: int = 20,
    message: str = "OK",
) -> Dict[str, Any]:
    """Build a paginated response dict."""
    return {
        "success": True,
        "timestamp": utc_now(),
        "data": items,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        },
        "message": message,
    }


# ─── Validation Helpers ──────────────────────────────────────────────

def validate_non_empty(value: Optional[str], field_name: str = "field") -> str:
    """Raise ValueError if value is None or empty after stripping."""
    if not value or not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value.strip()


def validate_user_id(user_id: Optional[str]) -> str:
    """Validate and return a cleaned user_id."""
    return validate_non_empty(user_id, "user_id")


def clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp a numeric value between min_val and max_val."""
    return max(min_val, min(max_val, value))


def safe_get(d: dict, *keys, default=None):
    """Safely traverse nested dicts."""
    current = d
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current


# ─── Error Response Creators ─────────────────────────────────────────

def not_found_error(resource: str = "Resource", identifier: str = "") -> Dict[str, Any]:
    """Create a 404-style error response."""
    msg = f"{resource} not found"
    if identifier:
        msg = f"{resource} '{identifier}' not found"
    return error_response(msg, code=404)


def validation_error(detail: str) -> Dict[str, Any]:
    """Create a 422-style validation error response."""
    return error_response("Validation error", detail=detail, code=422)


def internal_error(detail: str = "An internal error occurred") -> Dict[str, Any]:
    """Create a 500-style internal error response."""
    return error_response("Internal server error", detail=detail, code=500)
