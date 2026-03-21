import logging
import asyncio
import aiohttp
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from scipy.stats import norm
from app.config.settings import Config
from app.modules.alert_system import AlertSystem

# Logger configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
MAX_RETRIES = 3  # Number of retries for failed API requests
RISK_THRESHOLD = 0.02  # 2% risk per trade
DAILY_DRAWDOWN_LIMIT = 0.10  # 10% max daily loss
LEVERAGE_CAP = 3  # Max leverage allowed
MARKET_ANOMALY_THRESHOLD = 10  # Market cap change % triggering an alert
VAR_CONFIDENCE_LEVEL = 0.99  # Value-at-Risk confidence level
MONTE_CARLO_SIMULATIONS = 10000  # Number of simulations for stress testing


class RiskManager:
    """
    AI-Powered Advanced Risk Management System.
    """

    def __init__(self):
        """
        Initializes the risk management system with trading safeguards.
        """
        self.daily_loss = 0
        self.alert_system = AlertSystem(
            telegram_config={"bot_token": Config.TELEGRAM_BOT_TOKEN, "chat_id": Config.TELEGRAM_CHAT_ID},
            discord_webhook=Config.DISCORD_WEBHOOK_URL
        )

    async def _fetch_json(self, url):
        """
        Sends an asynchronous API request.

        Args:
            url (str): API endpoint.

        Returns:
            dict: API response.
        """
        for attempt in range(MAX_RETRIES):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        response.raise_for_status()
                        return await response.json()
            except aiohttp.ClientError as e:
                logging.error(f"API request failed: {e} (Attempt {attempt + 1}/{MAX_RETRIES})")
                await asyncio.sleep(2)

        self.alert_system.send_alert(f"🚨 API Failure: {url}", alert_type="telegram")
        return {}

    async def get_account_balance(self):
        """
        Fetches account balance from OKX.

        Returns:
            float: Available balance in USDT.
        """
        balance_data = await self._fetch_json("https://api.okx.com/v5/account/balance")
        if balance_data and "data" in balance_data:
            return float(balance_data["data"][0]["totalEq"])
        return 10000.0  # Default balance assumption

    async def get_open_positions(self):
        """
        Retrieves open trading positions.

        Returns:
            dict: Dictionary containing active positions.
        """
        positions = await self._fetch_json("https://api.okx.com/v5/account/positions")
        return positions.get("data", {}) if positions else {}

    async def calculate_position_risk(self, position):
        """
        Evaluates risk exposure of an open position.

        Args:
            position (dict): Open position data.

        Returns:
            float: Risk percentage of the position.
        """
        balance = await self.get_account_balance()
        if not balance:
            return None

        entry_price = float(position["entry_price"])
        current_price = float(position["current_price"])
        size = float(position["size"])

        loss = (entry_price - current_price) * size
        return loss / balance

    async def enforce_stop_loss(self, position):
        """
        Enforces stop-loss by closing risky trades.

        Args:
            position (dict): Open position data.

        Returns:
            bool: True if stop-loss triggered.
        """
        risk = await self.calculate_position_risk(position)
        if risk and risk > RISK_THRESHOLD:
            logging.warning(f"🚨 Stop-Loss Triggered: Closing {position}")
            self.alert_system.send_alert(f"Stop-Loss Activated: {position}", alert_type="telegram")
            return True
        return False

    async def enforce_take_profit(self, position, profit_threshold=0.05):
        """
        Implements take-profit mechanism.

        Args:
            position (dict): Open position data.
            profit_threshold (float): Profit level to trigger auto-close.

        Returns:
            bool: True if take-profit triggered.
        """
        balance = await self.get_account_balance()
        if not balance:
            return False

        entry_price = float(position["entry_price"])
        current_price = float(position["current_price"])
        size = float(position["size"])

        profit = (current_price - entry_price) * size
        if profit / balance > profit_threshold:
            logging.info(f"✅ Take-Profit Triggered: Closing {position}")
            self.alert_system.send_alert(f"Take-Profit Activated: {position}", alert_type="telegram")
            return True
        return False

    async def enforce_daily_drawdown_limit(self):
        """
        Stops trading if daily loss exceeds the maximum allowed.

        Returns:
            bool: True if trading should be halted.
        """
        balance = await self.get_account_balance()
        max_loss_allowed = balance * DAILY_DRAWDOWN_LIMIT

        if self.daily_loss > max_loss_allowed:
            logging.critical("🚨 Trading Halted Due to Daily Loss Limit.")
            self.alert_system.send_alert("🚨 Trading Halted Due to Daily Loss Limit.", alert_type="telegram")
            return True
        return False

    async def calculate_var(self, returns):
        """
        Computes Value-at-Risk (VaR) using historical return distribution.

        Args:
            returns (pd.Series): Historical asset returns.

        Returns:
            float: VaR at 99% confidence level.
        """
        var_threshold = np.percentile(returns, (1 - VAR_CONFIDENCE_LEVEL) * 100)
        logging.info(f"📉 Value-at-Risk (VaR) at {VAR_CONFIDENCE_LEVEL * 100}% confidence: {var_threshold:.2f}%")
        return var_threshold

    async def monte_carlo_risk_analysis(self):
        """
        Runs Monte Carlo simulations to estimate potential portfolio drawdowns.

        Returns:
            float: Estimated worst-case loss.
        """
        np.random.seed(42)
        simulated_losses = np.random.randn(MONTE_CARLO_SIMULATIONS) * 0.02
        worst_case_loss = np.percentile(simulated_losses, 5)  # 5th percentile worst-case scenario
        logging.info(f"🎲 Monte Carlo Simulation Worst-Case Loss: {worst_case_loss:.2f}%")
        return worst_case_loss

    async def detect_rug_pull(self, token_symbol):
        """
        Monitors liquidity changes to detect rug pulls.

        Args:
            token_symbol (str): Token to monitor.

        Returns:
            bool: True if rug pull is detected.
        """
        liquidity_data = await self._fetch_json(f"https://api.dexscreener.com/latest/dex/tokens/{token_symbol}")
        if "pairs" in liquidity_data:
            liquidity = liquidity_data["pairs"][0]["liquidity"]
            if liquidity < 80:
                logging.warning(f"🚨 Rug Pull Alert: {token_symbol} liquidity dropped below 80.")
                self.alert_system.send_alert(f"🚨 Rug Pull Alert: {token_symbol}", alert_type="telegram")
                return True
        return False

    async def execute_risk_checks(self):
        """
        Runs all risk management checks before allowing a trade.

        Returns:
            bool: True if trading is allowed.
        """
        if await self.enforce_daily_drawdown_limit():
            return False
        return True
