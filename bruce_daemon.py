#!/usr/bin/env python3
"""
Bruce AI — Autonomous Daemon

Runs Bruce as a background process that:
- Monitors markets 24/7
- Checks watchers and sends alerts
- Executes scheduled tasks
- Learns from new data automatically
- Self-analyzes and improves

Usage:
  python bruce_daemon.py                    # Run daemon
  python bruce_daemon.py --interval 60      # Check every 60 seconds
  python bruce_daemon.py --telegram BOT_TOKEN CHAT_ID  # Enable Telegram alerts
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("Bruce.Daemon")


class TelegramNotifier:
    """Send alerts to Federico via Telegram."""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = bool(bot_token and chat_id)

    def send(self, message: str) -> bool:
        if not self.enabled:
            return False
        try:
            import requests
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            r = requests.post(url, json={
                "chat_id": self.chat_id,
                "text": f"🦇 Bruce AI\n\n{message}",
                "parse_mode": "Markdown",
            }, timeout=10)
            return r.status_code == 200
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return False


class BruceDaemon:
    """Bruce running as an autonomous background process."""

    def __init__(self, interval: int = 300, telegram: TelegramNotifier = None):
        self.interval = interval
        self.telegram = telegram or TelegramNotifier("", "")
        self.bruce = None
        self.cycle_count = 0
        self.start_time = None

    def initialize(self):
        """Initialize Bruce."""
        logger.info("Initializing Bruce Daemon...")
        from bruce_agent import get_bruce
        self.bruce = get_bruce()
        self.start_time = datetime.now(timezone.utc)
        logger.info(f"Bruce ready | Brain: {self.bruce._llm_name} | Agents: {len(self.bruce.factory.agents)}")

        if self.telegram.enabled:
            self.telegram.send("Bruce Daemon started. Monitoring active.")

    def run_cycle(self):
        """Run one monitoring cycle."""
        self.cycle_count += 1
        logger.info(f"=== Cycle {self.cycle_count} ===")
        results = []

        # 1. Check market prices
        try:
            price_result = self.bruce.tools.execute("get_price", symbol="BTC/USDT")
            if price_result.success:
                data = json.loads(price_result.output)
                price = data.get("price", 0)
                change = data.get("change_24h", 0)
                results.append(f"BTC: ${price:,.2f} ({change:+.1f}%)")
                logger.info(f"BTC/USDT: ${price:,.2f} ({change:+.1f}%)")

                # Alert on big moves
                if abs(change or 0) > 5:
                    msg = f"⚠️ BTC big move: ${price:,.2f} ({change:+.1f}% in 24h)"
                    self.telegram.send(msg)
                    logger.warning(msg)
        except Exception as e:
            logger.debug(f"Price check: {e}")

        # 2. Check watchers
        try:
            health = self.bruce.monitor.health_check()
            state = {
                "error_rate": 100 - health.get("success_rate", 100),
                "avg_response_ms": health.get("avg_response_ms", 0),
            }
            triggered = self.bruce.check_intel(state)
            for alert in triggered:
                msg = f"🔔 Watcher: {alert['watcher']}\nCondition: {alert['condition']}\nAction: {alert['action']}"
                self.telegram.send(msg)
                logger.info(f"Watcher triggered: {alert['watcher']}")
                results.append(f"Alert: {alert['watcher']}")
        except Exception as e:
            logger.debug(f"Watcher check: {e}")

        # 3. Evaluate strategies
        try:
            strategy_result = self.bruce.tools.execute(
                "evaluate_strategy", strategy="rsi", symbol="BTC/USDT"
            )
            if strategy_result.success:
                signal = json.loads(strategy_result.output)
                sig = signal.get("signal", "HOLD")
                confidence = signal.get("confidence", 0)
                results.append(f"RSI Signal: {sig} ({confidence:.0%})")

                if sig in ("BUY", "SELL") and confidence > 0.7:
                    msg = f"📊 Trading Signal: {sig} BTC/USDT (confidence: {confidence:.0%})"
                    self.telegram.send(msg)
        except Exception as e:
            logger.debug(f"Strategy eval: {e}")

        # 4. Self-analysis (every 10 cycles)
        if self.cycle_count % 10 == 0:
            try:
                analysis = self.bruce.self_analyze()
                for s in analysis.get("suggestions", []):
                    if s["priority"] in ("critical", "high"):
                        logger.warning(f"Self-analysis: [{s['priority']}] {s['suggestion']}")
            except Exception:
                pass

        # 5. Record cycle
        self.bruce.monitor.record_response(self.interval * 1000, True)

        if results:
            logger.info(f"Cycle {self.cycle_count} results: {' | '.join(results)}")

    def run(self):
        """Run the daemon loop."""
        self.initialize()

        logger.info(f"Daemon running | Interval: {self.interval}s | Telegram: {self.telegram.enabled}")
        print(f"\n{'='*60}")
        print(f"  Bruce Daemon Active")
        print(f"  Interval: {self.interval}s | Brain: {self.bruce._llm_name}")
        print(f"  Telegram: {'ON' if self.telegram.enabled else 'OFF'}")
        print(f"  Press Ctrl+C to stop")
        print(f"{'='*60}\n")

        try:
            while True:
                self.run_cycle()
                time.sleep(self.interval)
        except KeyboardInterrupt:
            uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()
            logger.info(f"Daemon stopped | Cycles: {self.cycle_count} | Uptime: {uptime:.0f}s")
            if self.telegram.enabled:
                self.telegram.send(f"Bruce Daemon stopped.\nCycles: {self.cycle_count}\nUptime: {uptime:.0f}s")
            print(f"\nBruce Daemon stopped. {self.cycle_count} cycles completed.")


def main():
    parser = argparse.ArgumentParser(description="Bruce AI Autonomous Daemon")
    parser.add_argument("--interval", type=int, default=300, help="Check interval in seconds (default: 300)")
    parser.add_argument("--telegram", nargs=2, metavar=("BOT_TOKEN", "CHAT_ID"), help="Telegram bot token and chat ID")
    args = parser.parse_args()

    telegram = None
    if args.telegram:
        telegram = TelegramNotifier(args.telegram[0], args.telegram[1])
    elif os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"):
        telegram = TelegramNotifier(
            os.environ["TELEGRAM_BOT_TOKEN"],
            os.environ["TELEGRAM_CHAT_ID"],
        )

    daemon = BruceDaemon(interval=args.interval, telegram=telegram)
    daemon.run()


if __name__ == "__main__":
    main()
