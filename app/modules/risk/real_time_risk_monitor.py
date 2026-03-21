import logging
import asyncio
import numpy as np
from app.utils.database import DatabaseManager

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
VOLATILITY_SPIKE_THRESHOLD = 0.05  # 5% volatility spike triggers alerts
LIQUIDITY_DROP_THRESHOLD = 0.1  # 10% liquidity drop triggers alert
RISK_MONITOR_INTERVAL = 300  # Check every 5 minutes

class RealTimeRiskMonitor:
    """
    AI-Powered Real-Time Risk Monitoring System.
    """

    def __init__(self):
        """
        Initializes the risk monitoring engine.
        """
        self.db_manager = DatabaseManager()

    async def check_volatility_spikes(self):
        """
        Detects sudden market volatility increases.
        """
        historical_volatility = await self.db_manager.get_historical_volatility()
        current_volatility = await self.db_manager.get_current_volatility()

        if current_volatility - historical_volatility > VOLATILITY_SPIKE_THRESHOLD:
            logging.warning(f"⚠️ Volatility Spike Detected: {current_volatility:.2f}")
            return f"🚨 Volatility Alert: {current_volatility:.2f}"

        return "No volatility spikes detected"

    async def check_liquidity_risk(self):
        """
        Monitors market liquidity for sudden drops.
        """
        liquidity_data = await self.db_manager.get_market_liquidity()
        if liquidity_data["drop_percentage"] > LIQUIDITY_DROP_THRESHOLD:
            logging.critical(f"🚨 Liquidity Drop Alert: {liquidity_data['drop_percentage']:.2f}%")
            return f"🚨 Liquidity Drop Alert: {liquidity_data['drop_percentage']:.2f}%"

        return "Liquidity stable"

    async def calculate_portfolio_risk_score(self):
        """
        Generates an AI-powered risk score for the portfolio.
        """
        market_risk = await self.db_manager.get_market_risk_factor()
        exposure = await self.db_manager.get_portfolio_exposure()
        risk_score = market_risk * exposure

        logging.info(f"📊 AI Risk Score: {risk_score:.2f}")
        return risk_score

    async def run_risk_monitoring(self):
        """
        Runs continuous risk monitoring and alerts.
        """
        while True:
            await self.check_volatility_spikes()
            await self.check_liquidity_risk()
            await self.calculate_portfolio_risk_score()
            await asyncio.sleep(RISK_MONITOR_INTERVAL)

# Example Usage
if __name__ == "__main__":
    risk_monitor = RealTimeRiskMonitor()
    asyncio.run(risk_monitor.run_risk_monitoring())
