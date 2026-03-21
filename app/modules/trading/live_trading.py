import asyncio
import logging
import signal
import sys
from app.modules.trading.trade_execution import TradeExecution
from app.modules.machine_learning.reinforcement_learning import ReinforcementLearningAgent
from app.config.settings import Config

# Logger configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class LiveTradingBot:
    """
    AI-Powered Live Trading System for Real-Time Execution.
    """

    def __init__(self):
        """
        Initializes the live trading bot.
        """
        self.trade_executor = TradeExecution()
        self.rl_agent = ReinforcementLearningAgent()
        self.running = True

    async def trade_loop(self):
        """
        Runs the live trading loop, continuously predicting and executing trades.
        """
        logging.info("🚀 Live Trading Bot Started!")
        while self.running:
            try:
                action = await self.rl_agent.predict_trade_action()
                if action in ["BUY", "SELL"]:
                    await self.trade_executor.execute_trade(action)

                await asyncio.sleep(0.5)  # Adjust frequency based on exchange rate limits
            except Exception as e:
                logging.error(f"❌ Error in live trading loop: {e}")

    def stop(self, sig, frame):
        """
        Handles shutdown signals to stop the bot gracefully.
        """
        logging.info("🛑 Stopping Live Trading Bot...")
        self.running = False
        sys.exit(0)

    def start(self):
        """
        Starts the bot and handles termination signals.
        """
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
        asyncio.run(self.trade_loop())

# Run Live Trading Bot
if __name__ == "__main__":
    bot = LiveTradingBot()
    bot.start()
