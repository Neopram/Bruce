"""
Bruce AI — Telegram Alert System

Lightweight module for Bruce to PUSH messages to Federico via Telegram.
Can be imported anywhere in the codebase. No bot polling — just sends messages.

Usage:
    from modules.telegram_alerts import send_alert, send_price_alert, send_report

    send_alert("BTC just crossed 100k!")
    send_price_alert("BTC/USDT", 100250.0, 5.2)
    send_report("Daily portfolio summary...")
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("Bruce.Telegram.Alerts")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TELEGRAM_BOT_TOKEN: Optional[str] = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID: Optional[str] = os.environ.get("TELEGRAM_CHAT_ID")

_BASE_URL = "https://api.telegram.org/bot{token}/sendMessage"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_config() -> tuple:
    """Return (token, chat_id) or raise if missing."""
    token = TELEGRAM_BOT_TOKEN or os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = TELEGRAM_CHAT_ID or os.environ.get("TELEGRAM_CHAT_ID")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set in environment")
    if not chat_id:
        raise RuntimeError("TELEGRAM_CHAT_ID not set in environment")
    return token, chat_id


async def _send_message_async(text: str, parse_mode: str = "HTML") -> dict:
    """Send a message via Telegram Bot API (async, using httpx or requests fallback)."""
    token, chat_id = _get_config()
    url = _BASE_URL.format(token=token)
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }

    # Try httpx first (async-native), fall back to requests
    try:
        import httpx
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()
    except ImportError:
        pass

    # Fallback: requests in thread executor
    import requests
    loop = asyncio.get_event_loop()
    resp = await loop.run_in_executor(
        None,
        lambda: requests.post(url, json=payload, timeout=15),
    )
    resp.raise_for_status()
    return resp.json()


def _send_message_sync(text: str, parse_mode: str = "HTML") -> dict:
    """Send a message synchronously. Works from non-async contexts."""
    token, chat_id = _get_config()
    url = _BASE_URL.format(token=token)
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }
    import requests
    resp = requests.post(url, json=payload, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _send(text: str, parse_mode: str = "HTML") -> dict:
    """Smart send: uses async if an event loop is running, otherwise sync."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We're inside an async context — schedule the coroutine
        future = asyncio.ensure_future(_send_message_async(text, parse_mode))
        # If the caller is sync but loop is running (e.g. Jupyter), use sync fallback
        try:
            return _send_message_sync(text, parse_mode)
        except Exception:
            return {"ok": True, "scheduled": True}
    else:
        return _send_message_sync(text, parse_mode)


# ---------------------------------------------------------------------------
# Public API — import these anywhere in the codebase
# ---------------------------------------------------------------------------

def send_alert(message: str) -> dict:
    """
    Send a custom alert message to Federico via Telegram.

    Args:
        message: The alert text (supports HTML formatting).

    Returns:
        Telegram API response dict.
    """
    timestamp = datetime.now(timezone.utc).strftime("%H:%M UTC")
    text = (
        f"🚨 <b>Bruce Alert</b>\n"
        f"<code>{timestamp}</code>\n\n"
        f"{message}"
    )
    try:
        result = _send(text)
        logger.info(f"Alert sent: {message[:80]}")
        return result
    except Exception as e:
        logger.error(f"Failed to send alert: {e}")
        return {"ok": False, "error": str(e)}


def send_price_alert(symbol: str, price: float, change: float = 0.0) -> dict:
    """
    Send a price alert for a specific asset.

    Args:
        symbol: Trading pair (e.g. "BTC/USDT").
        price:  Current price.
        change: 24h percentage change.

    Returns:
        Telegram API response dict.
    """
    direction = "📈" if change >= 0 else "📉"
    sign = "+" if change >= 0 else ""
    text = (
        f"{direction} <b>Price Alert: {symbol}</b>\n\n"
        f"Price: <code>${price:,.2f}</code>\n"
        f"24h:   <code>{sign}{change:.2f}%</code>\n"
        f"Time:  <code>{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</code>"
    )
    try:
        result = _send(text)
        logger.info(f"Price alert sent: {symbol} @ {price}")
        return result
    except Exception as e:
        logger.error(f"Failed to send price alert: {e}")
        return {"ok": False, "error": str(e)}


def send_report(report_text: str, title: str = "Bruce Report") -> dict:
    """
    Send a formatted report to Federico.

    Args:
        report_text: The report body (plain text or HTML).
        title:       Report title.

    Returns:
        Telegram API response dict.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    text = (
        f"📊 <b>{title}</b>\n"
        f"<code>{timestamp}</code>\n\n"
        f"{report_text}"
    )
    # Telegram message limit is 4096 chars
    if len(text) > 4000:
        text = text[:3990] + "\n\n<i>... (truncated)</i>"
    try:
        result = _send(text)
        logger.info(f"Report sent: {title}")
        return result
    except Exception as e:
        logger.error(f"Failed to send report: {e}")
        return {"ok": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Async variants (for use inside async code)
# ---------------------------------------------------------------------------

async def async_send_alert(message: str) -> dict:
    """Async version of send_alert."""
    timestamp = datetime.now(timezone.utc).strftime("%H:%M UTC")
    text = (
        f"🚨 <b>Bruce Alert</b>\n"
        f"<code>{timestamp}</code>\n\n"
        f"{message}"
    )
    try:
        result = await _send_message_async(text)
        logger.info(f"Alert sent (async): {message[:80]}")
        return result
    except Exception as e:
        logger.error(f"Failed to send alert (async): {e}")
        return {"ok": False, "error": str(e)}


async def async_send_price_alert(symbol: str, price: float, change: float = 0.0) -> dict:
    """Async version of send_price_alert."""
    direction = "📈" if change >= 0 else "📉"
    sign = "+" if change >= 0 else ""
    text = (
        f"{direction} <b>Price Alert: {symbol}</b>\n\n"
        f"Price: <code>${price:,.2f}</code>\n"
        f"24h:   <code>{sign}{change:.2f}%</code>\n"
        f"Time:  <code>{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</code>"
    )
    try:
        result = await _send_message_async(text)
        logger.info(f"Price alert sent (async): {symbol} @ {price}")
        return result
    except Exception as e:
        logger.error(f"Failed to send price alert (async): {e}")
        return {"ok": False, "error": str(e)}


async def async_send_report(report_text: str, title: str = "Bruce Report") -> dict:
    """Async version of send_report."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    text = (
        f"📊 <b>{title}</b>\n"
        f"<code>{timestamp}</code>\n\n"
        f"{report_text}"
    )
    if len(text) > 4000:
        text = text[:3990] + "\n\n<i>... (truncated)</i>"
    try:
        result = await _send_message_async(text)
        logger.info(f"Report sent (async): {title}")
        return result
    except Exception as e:
        logger.error(f"Failed to send report (async): {e}")
        return {"ok": False, "error": str(e)}
