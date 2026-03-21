
import asyncio
import logging

from app.services.ai.model import PredictiveAI
from app.services.blockchain.defi import execute_trade
from app.services.risk.risk_engine import check_risk_limits

logger = logging.getLogger(__name__)
ai = PredictiveAI()

async def run_ai_and_execute_trade():
    while True:
        try:
            prediction = ai.predict()
            logger.info(f"🤖 Predicción AI: {prediction}")
            if prediction > 0.7 and check_risk_limits():
                await execute_trade("ETH", 0.01)
                logger.info("💰 Trade ejecutado por IA")
        except Exception as e:
            logger.error(f"❌ Error en tarea AI: {str(e)}")
        await asyncio.sleep(60)
