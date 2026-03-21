"""
Bruce AI — Telegram Bot Interface

Full Telegram bot that connects Federico to Bruce via chat.
Supports commands, text forwarding, and a push alert system.

Start standalone:
    TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=123 python -m modules.telegram_bot

Or import and run:
    from modules.telegram_bot import BruceTelegramBot
    bot = BruceTelegramBot()
    bot.run()
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logger = logging.getLogger("Bruce.Telegram.Bot")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TELEGRAM_BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.environ.get("TELEGRAM_CHAT_ID", "")


# ---------------------------------------------------------------------------
# Authorization decorator
# ---------------------------------------------------------------------------

def authorized_only(func):
    """Decorator that restricts a handler to the authorized chat ID only."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.effective_chat.id)
        authorized = TELEGRAM_CHAT_ID or os.environ.get("TELEGRAM_CHAT_ID", "")
        if not authorized:
            logger.warning("TELEGRAM_CHAT_ID not set — rejecting all messages")
            return
        if chat_id != authorized:
            logger.warning(f"Unauthorized access attempt from chat_id={chat_id}")
            await update.message.reply_text("Access denied.")
            return
        return await func(update, context)
    return wrapper


# ---------------------------------------------------------------------------
# Alert system — price watchers & scheduled reports
# ---------------------------------------------------------------------------

class AlertManager:
    """Manages price alerts, custom alerts, and scheduled reports."""

    def __init__(self, application: Application):
        self.app = application
        self.price_alerts: List[Dict] = []
        self.scheduled_reports: List[Dict] = []
        self._price_check_task: Optional[asyncio.Task] = None
        self._report_tasks: List[asyncio.Task] = []

    async def start(self):
        """Start background alert monitors."""
        self._price_check_task = asyncio.create_task(self._price_monitor_loop())
        logger.info("Alert manager started")

    async def stop(self):
        """Stop all background tasks."""
        if self._price_check_task:
            self._price_check_task.cancel()
        for task in self._report_tasks:
            task.cancel()
        logger.info("Alert manager stopped")

    # --- Price alerts ---

    def add_price_alert(
        self, symbol: str, condition: str, threshold: float
    ) -> dict:
        """
        Add a price alert.

        Args:
            symbol:    e.g. "BTC/USDT"
            condition: "above" or "below"
            threshold: price level to trigger at
        """
        alert = {
            "id": len(self.price_alerts) + 1,
            "symbol": symbol.upper(),
            "condition": condition.lower(),
            "threshold": float(threshold),
            "triggered": False,
            "created": datetime.now(timezone.utc).isoformat(),
        }
        self.price_alerts.append(alert)
        logger.info(f"Price alert added: {symbol} {condition} {threshold}")
        return alert

    async def _price_monitor_loop(self):
        """Background loop that checks prices against alert thresholds."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every 60 seconds
                active_alerts = [a for a in self.price_alerts if not a["triggered"]]
                if not active_alerts:
                    continue

                # Group alerts by symbol to minimize API calls
                symbols = set(a["symbol"] for a in active_alerts)
                for symbol in symbols:
                    try:
                        price = await self._fetch_price(symbol)
                        if price is None:
                            continue
                        for alert in active_alerts:
                            if alert["symbol"] != symbol:
                                continue
                            triggered = False
                            if alert["condition"] == "above" and price >= alert["threshold"]:
                                triggered = True
                            elif alert["condition"] == "below" and price <= alert["threshold"]:
                                triggered = True

                            if triggered:
                                alert["triggered"] = True
                                await self._send_alert_notification(
                                    f"Price Alert Triggered!\n\n"
                                    f"{symbol}: ${price:,.2f}\n"
                                    f"Condition: {alert['condition']} ${alert['threshold']:,.2f}"
                                )
                    except Exception as e:
                        logger.debug(f"Price check failed for {symbol}: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Price monitor error: {e}")
                await asyncio.sleep(30)

    async def _fetch_price(self, symbol: str) -> Optional[float]:
        """Fetch current price via ccxt (run in executor to avoid blocking)."""
        loop = asyncio.get_event_loop()

        def _get():
            try:
                import ccxt
                exchange = ccxt.binance()
                ticker = exchange.fetch_ticker(symbol)
                return ticker.get("last")
            except Exception as e:
                logger.debug(f"ccxt price fetch error: {e}")
                return None

        return await loop.run_in_executor(None, _get)

    # --- Custom alerts ---

    async def custom_alert(self, message: str):
        """Send a one-off custom alert immediately."""
        await self._send_alert_notification(message)

    # --- Scheduled reports ---

    def add_scheduled_report(
        self, interval_seconds: int, report_fn: Callable, label: str = "Report"
    ) -> dict:
        """
        Schedule a recurring report.

        Args:
            interval_seconds: How often to send (e.g. 3600 = hourly).
            report_fn:        Callable that returns a string report.
            label:            Human-readable label.
        """
        report = {
            "id": len(self.scheduled_reports) + 1,
            "interval": interval_seconds,
            "label": label,
            "active": True,
        }
        self.scheduled_reports.append(report)
        task = asyncio.create_task(
            self._report_loop(report, report_fn)
        )
        self._report_tasks.append(task)
        logger.info(f"Scheduled report: '{label}' every {interval_seconds}s")
        return report

    async def _report_loop(self, report: dict, report_fn: Callable):
        """Background loop that sends periodic reports."""
        while report["active"]:
            try:
                await asyncio.sleep(report["interval"])
                loop = asyncio.get_event_loop()
                text = await loop.run_in_executor(None, report_fn)
                await self._send_alert_notification(
                    f"Scheduled Report: {report['label']}\n\n{text}"
                )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Report loop error ({report['label']}): {e}")
                await asyncio.sleep(60)

    # --- Internal ---

    async def _send_alert_notification(self, text: str):
        """Send a notification to the authorized chat."""
        chat_id = TELEGRAM_CHAT_ID or os.environ.get("TELEGRAM_CHAT_ID", "")
        if not chat_id:
            logger.warning("Cannot send alert: TELEGRAM_CHAT_ID not set")
            return
        timestamp = datetime.now(timezone.utc).strftime("%H:%M UTC")
        full_text = f"🤖 <b>Bruce AI</b> <code>{timestamp}</code>\n\n{text}"
        if len(full_text) > 4000:
            full_text = full_text[:3990] + "\n\n<i>... (truncated)</i>"
        try:
            await self.app.bot.send_message(
                chat_id=int(chat_id),
                text=full_text,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")


# ---------------------------------------------------------------------------
# Main Bot class
# ---------------------------------------------------------------------------

class BruceTelegramBot:
    """
    Telegram interface for Bruce AI.

    Provides command handlers, text forwarding to Bruce's agent,
    and a push alert system.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        chat_id: Optional[str] = None,
        bruce_agent: Optional[Any] = None,
    ):
        self.token = token or TELEGRAM_BOT_TOKEN or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or TELEGRAM_CHAT_ID or os.environ.get("TELEGRAM_CHAT_ID", "")

        if not self.token:
            raise ValueError(
                "Telegram bot token required. Set TELEGRAM_BOT_TOKEN env var "
                "or pass token= to constructor."
            )

        # Bruce agent (lazy-loaded if not provided)
        self._bruce = bruce_agent
        self._bruce_loaded = bruce_agent is not None

        # Build the application
        self.app = Application.builder().token(self.token).build()
        self.alerts = AlertManager(self.app)

        # Register handlers
        self._register_handlers()
        logger.info("BruceTelegramBot initialized")

    def _get_bruce(self):
        """Lazy-load Bruce agent on first use."""
        if not self._bruce_loaded:
            try:
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from bruce_agent import BruceAgent
                self._bruce = BruceAgent()
                self._bruce_loaded = True
                logger.info("Bruce agent loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Bruce agent: {e}")
                self._bruce = None
                self._bruce_loaded = True
        return self._bruce

    def _register_handlers(self):
        """Register all command and message handlers."""
        self.app.add_handler(CommandHandler("start", self._cmd_start))
        self.app.add_handler(CommandHandler("status", self._cmd_status))
        self.app.add_handler(CommandHandler("price", self._cmd_price))
        self.app.add_handler(CommandHandler("agents", self._cmd_agents))
        self.app.add_handler(CommandHandler("swarm", self._cmd_swarm))
        self.app.add_handler(CommandHandler("goal", self._cmd_goal))
        self.app.add_handler(CommandHandler("reflect", self._cmd_reflect))
        self.app.add_handler(CommandHandler("alert", self._cmd_alert))
        self.app.add_handler(CommandHandler("help", self._cmd_help))

        # Catch-all: forward text messages to Bruce chat
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text)
        )

        # Post-init hook to start alert manager
        self.app.post_init = self._on_startup

    async def _on_startup(self, application: Application):
        """Called after the application is initialized."""
        await self.alerts.start()
        logger.info("Telegram bot started and alert manager running")

    # -----------------------------------------------------------------------
    # Command handlers
    # -----------------------------------------------------------------------

    @authorized_only
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start — welcome message."""
        text = (
            "🦇 <b>Bruce AI — Online</b>\n\n"
            "I'm your autonomous AI agent. Here's what I can do:\n\n"
            "/status  — Full system status\n"
            "/price &lt;symbol&gt; — Live crypto price\n"
            "/agents — List micro-agents\n"
            "/swarm &lt;question&gt; — Swarm analysis\n"
            "/goal &lt;title&gt; — Set a new goal\n"
            "/reflect — Self-reflection\n"
            "/alert &lt;symbol&gt; &lt;above|below&gt; &lt;price&gt; — Price alert\n"
            "/help — This message\n\n"
            "Or just type anything and I'll respond.\n\n"
            f"<code>Chat ID: {update.effective_chat.id}</code>"
        )
        await update.message.reply_text(text, parse_mode="HTML")

    @authorized_only
    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status — Bruce's full status report."""
        bruce = self._get_bruce()
        if not bruce:
            await update.message.reply_text("Bruce agent not available.")
            return

        try:
            status = bruce.status()
            identity = status.get("identity", {})
            health = status.get("health", {})

            text = (
                "📊 <b>Bruce AI — Status</b>\n\n"
                f"Name: <code>{identity.get('name', 'Bruce')}</code>\n"
                f"Version: <code>{identity.get('version', 'unknown')}</code>\n"
                f"Status: <code>{identity.get('status', 'unknown')}</code>\n"
                f"LLM: <code>{status.get('llm', 'none')}</code>\n"
                f"Active: <code>{status.get('active', False)}</code>\n\n"
                f"<b>Agents:</b> {json.dumps(status.get('agents', {}), indent=2)}\n"
                f"<b>Goals:</b> {status.get('goals', 0)}\n"
                f"<b>Watchers:</b> {status.get('watchers', 0)}\n"
                f"<b>Conversations:</b> {status.get('conversation_length', 0)}\n\n"
                f"<b>Health:</b>\n<code>{json.dumps(health, indent=2)}</code>"
            )
            # Truncate if too long
            if len(text) > 4000:
                text = text[:3990] + "\n\n<i>... (truncated)</i>"
            await update.message.reply_text(text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"/status error: {e}")
            await update.message.reply_text(f"Status error: {e}")

    @authorized_only
    async def _cmd_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /price <symbol> — get live price from CCXT."""
        if not context.args:
            await update.message.reply_text(
                "Usage: /price BTC/USDT\n\nExamples: BTC/USDT, ETH/USDT, SOL/USDT"
            )
            return

        symbol = context.args[0].upper()
        if "/" not in symbol:
            symbol += "/USDT"

        await update.message.reply_text(f"Fetching {symbol}...")

        loop = asyncio.get_event_loop()

        def _fetch():
            try:
                import ccxt
                exchange = ccxt.binance()
                ticker = exchange.fetch_ticker(symbol)
                return ticker
            except Exception as e:
                return {"error": str(e)}

        ticker = await loop.run_in_executor(None, _fetch)

        if "error" in ticker:
            await update.message.reply_text(f"Error: {ticker['error']}")
            return

        price = ticker.get("last", 0)
        change = ticker.get("percentage", 0) or 0
        volume = ticker.get("quoteVolume", 0) or 0
        high = ticker.get("high", 0) or 0
        low = ticker.get("low", 0) or 0

        direction = "📈" if change >= 0 else "📉"
        sign = "+" if change >= 0 else ""

        text = (
            f"{direction} <b>{symbol}</b>\n\n"
            f"Price:  <code>${price:,.2f}</code>\n"
            f"24h:    <code>{sign}{change:.2f}%</code>\n"
            f"High:   <code>${high:,.2f}</code>\n"
            f"Low:    <code>${low:,.2f}</code>\n"
            f"Volume: <code>${volume:,.0f}</code>"
        )
        await update.message.reply_text(text, parse_mode="HTML")

    @authorized_only
    async def _cmd_agents(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /agents — list micro-agents."""
        bruce = self._get_bruce()
        if not bruce:
            await update.message.reply_text("Bruce agent not available.")
            return

        try:
            agents_list = bruce.factory.list_agents()
            if not agents_list:
                await update.message.reply_text("No micro-agents currently active.")
                return

            lines = ["🤖 <b>Micro-Agents</b>\n"]
            for agent in agents_list:
                name = agent.get("name", "unknown")
                role = agent.get("role", "general")
                status = agent.get("status", "idle")
                tasks = agent.get("tasks_completed", 0)
                lines.append(
                    f"  <b>{name}</b> [{role}]\n"
                    f"    Status: <code>{status}</code> | Tasks: <code>{tasks}</code>"
                )

            text = "\n".join(lines)
            if len(text) > 4000:
                text = text[:3990] + "\n\n<i>... (truncated)</i>"
            await update.message.reply_text(text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"/agents error: {e}")
            await update.message.reply_text(f"Error listing agents: {e}")

    @authorized_only
    async def _cmd_swarm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /swarm <question> — run swarm analysis."""
        if not context.args:
            await update.message.reply_text("Usage: /swarm <question>\n\nExample: /swarm Should I buy ETH now?")
            return

        question = " ".join(context.args)
        bruce = self._get_bruce()
        if not bruce:
            await update.message.reply_text("Bruce agent not available.")
            return

        await update.message.reply_text(f"Running swarm analysis on: {question}...")

        loop = asyncio.get_event_loop()

        def _run_swarm():
            try:
                # Use Bruce's factory to run a swarm consultation
                result = bruce.factory.swarm_consult(question)
                return result
            except AttributeError:
                # Fallback: use Bruce's chat with swarm context
                return bruce.chat(
                    f"[SWARM ANALYSIS] Analyze this from multiple perspectives "
                    f"(trader, risk analyst, macro strategist): {question}"
                )
            except Exception as e:
                return f"Swarm error: {e}"

        result = await loop.run_in_executor(None, _run_swarm)

        if isinstance(result, dict):
            text = f"🐝 <b>Swarm Analysis</b>\n\n<code>{json.dumps(result, indent=2, default=str)[:3500]}</code>"
        else:
            text = f"🐝 <b>Swarm Analysis</b>\n\n{str(result)[:3500]}"

        if len(text) > 4000:
            text = text[:3990] + "\n\n<i>... (truncated)</i>"
        await update.message.reply_text(text, parse_mode="HTML")

    @authorized_only
    async def _cmd_goal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /goal <title> — set a new goal."""
        if not context.args:
            await update.message.reply_text("Usage: /goal <title>\n\nExample: /goal Build portfolio tracker")
            return

        title = " ".join(context.args)
        bruce = self._get_bruce()
        if not bruce:
            await update.message.reply_text("Bruce agent not available.")
            return

        try:
            goal = bruce.planner.add_goal(title)
            text = (
                f"🎯 <b>Goal Set</b>\n\n"
                f"Title: <code>{title}</code>\n"
                f"ID: <code>{goal.get('id', 'N/A')}</code>\n"
                f"Status: <code>{goal.get('status', 'active')}</code>"
            )
            await update.message.reply_text(text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"/goal error: {e}")
            await update.message.reply_text(f"Error setting goal: {e}")

    @authorized_only
    async def _cmd_reflect(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /reflect — trigger self-reflection."""
        bruce = self._get_bruce()
        if not bruce:
            await update.message.reply_text("Bruce agent not available.")
            return

        await update.message.reply_text("Reflecting...")

        loop = asyncio.get_event_loop()

        def _reflect():
            try:
                return bruce.reflect()
            except Exception as e:
                return f"Reflection error: {e}"

        reflection = await loop.run_in_executor(None, _reflect)

        text = f"🪞 <b>Self-Reflection</b>\n\n<pre>{str(reflection)[:3500]}</pre>"
        if len(text) > 4000:
            text = text[:3990] + "\n\n<i>... (truncated)</i>"
        await update.message.reply_text(text, parse_mode="HTML")

    @authorized_only
    async def _cmd_alert(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /alert <symbol> <above|below> <price> — set a price alert."""
        if not context.args or len(context.args) < 3:
            await update.message.reply_text(
                "Usage: /alert &lt;symbol&gt; &lt;above|below&gt; &lt;price&gt;\n\n"
                "Example: /alert BTC/USDT above 100000"
            )
            return

        symbol = context.args[0].upper()
        condition = context.args[1].lower()
        try:
            threshold = float(context.args[2])
        except ValueError:
            await update.message.reply_text("Price must be a number.")
            return

        if condition not in ("above", "below"):
            await update.message.reply_text("Condition must be 'above' or 'below'.")
            return

        if "/" not in symbol:
            symbol += "/USDT"

        alert = self.alerts.add_price_alert(symbol, condition, threshold)
        text = (
            f"🔔 <b>Price Alert Set</b>\n\n"
            f"Symbol: <code>{symbol}</code>\n"
            f"Trigger: <code>{condition} ${threshold:,.2f}</code>\n"
            f"Alert ID: <code>{alert['id']}</code>\n\n"
            f"I'll notify you when the condition is met."
        )
        await update.message.reply_text(text, parse_mode="HTML")

    @authorized_only
    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help — show commands."""
        await self._cmd_start(update, context)

    # -----------------------------------------------------------------------
    # Text message handler — forward to Bruce chat
    # -----------------------------------------------------------------------

    @authorized_only
    async def _handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Forward any text message to Bruce's chat interface."""
        message = update.message.text
        bruce = self._get_bruce()

        if not bruce:
            await update.message.reply_text(
                "Bruce agent is not available. Check logs for details."
            )
            return

        # Show typing indicator
        await update.message.chat.send_action("typing")

        loop = asyncio.get_event_loop()

        def _chat():
            try:
                return bruce.chat(message)
            except Exception as e:
                return f"Error: {e}"

        response = await loop.run_in_executor(None, _chat)

        # Split long responses into multiple messages
        if len(response) > 4000:
            chunks = [response[i:i + 4000] for i in range(0, len(response), 4000)]
            for chunk in chunks[:5]:  # Max 5 chunks
                await update.message.reply_text(chunk)
        else:
            await update.message.reply_text(response)

    # -----------------------------------------------------------------------
    # Public API — for external push alerts
    # -----------------------------------------------------------------------

    async def push_message(self, text: str, parse_mode: str = "HTML"):
        """Push a message to the authorized chat (for use by other modules)."""
        chat_id = self.chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")
        if not chat_id:
            logger.warning("Cannot push message: TELEGRAM_CHAT_ID not set")
            return
        await self.app.bot.send_message(
            chat_id=int(chat_id), text=text, parse_mode=parse_mode
        )

    def price_alert(self, symbol: str, condition: str, threshold: float) -> dict:
        """Add a price alert (convenience method)."""
        return self.alerts.add_price_alert(symbol, condition, threshold)

    async def custom_alert(self, message: str):
        """Send a custom alert (convenience method)."""
        await self.alerts.custom_alert(message)

    def scheduled_report(self, interval: int, report_fn: Callable, label: str = "Report") -> dict:
        """Schedule a recurring report (convenience method)."""
        return self.alerts.add_scheduled_report(interval, report_fn, label)

    # -----------------------------------------------------------------------
    # Run
    # -----------------------------------------------------------------------

    def run(self):
        """Start the bot (blocking). Use for standalone execution."""
        logger.info("Starting Bruce Telegram Bot...")
        self.app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

def main():
    """Run the Telegram bot standalone."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if not os.environ.get("TELEGRAM_BOT_TOKEN"):
        print("ERROR: Set TELEGRAM_BOT_TOKEN environment variable")
        sys.exit(1)
    if not os.environ.get("TELEGRAM_CHAT_ID"):
        print("WARNING: TELEGRAM_CHAT_ID not set — bot will reject all messages")

    bot = BruceTelegramBot()
    bot.run()


if __name__ == "__main__":
    main()
