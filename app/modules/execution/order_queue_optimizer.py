import logging
import asyncio
import numpy as np
from app.modules.execution.smart_order_router import SmartOrderRouter
from app.modules.analytics.order_flow_analyzer import OrderFlowAnalyzer
from app.config.settings import Config

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
ORDER_QUEUE_LOOKBACK = 50  # Number of orders analyzed
MAX_ORDER_QUEUE_TIME = 1.5  # Max time (seconds) allowed in queue
ORDER_REORDERING_THRESHOLD = 0.01  # Order adjustments allowed for best fill


class OrderQueueOptimizer:
    """
    AI-Powered Order Queue Optimization & Execution Flow Enhancements.
    """

    def __init__(self):
        self.smart_order_router = SmartOrderRouter()
        self.order_flow_analyzer = OrderFlowAnalyzer()

    async def analyze_order_queue(self):
        """
        Analyzes current order queue latency.
        """
        queued_orders = await self.smart_order_router.get_order_queue()
        if not queued_orders:
            return None

        queue_times = [order["execution_time"] for order in queued_orders]
        avg_queue_time = np.mean(queue_times)

        logging.info(f"📊 Average Order Queue Time: {avg_queue_time:.3f}s")
        return avg_queue_time

    async def adjust_order_queue(self):
        """
        Dynamically adjusts the order queue for optimal execution.
        """
        avg_queue_time = await self.analyze_order_queue()
        if avg_queue_time and avg_queue_time > MAX_ORDER_QUEUE_TIME:
            logging.warning("⚠️ High Order Queue Latency Detected. Adjusting Execution...")
            await self.reorder_orders()

    async def reorder_orders(self):
        """
        AI-Powered Order Reordering for Best Execution.
        """
        queued_orders = await self.smart_order_router.get_order_queue()
        if not queued_orders:
            return

        sorted_orders = sorted(queued_orders, key=lambda x: x["execution_priority"], reverse=True)

        for order in sorted_orders:
            if order["adjustment_allowed"] > ORDER_REORDERING_THRESHOLD:
                logging.info(f"🔄 Reordering Order: {order['order_id']} for better execution.")
                await self.smart_order_router.modify_order(order["order_id"], new_price=order["optimized_price"])

    async def optimize_order_execution(self):
        """
        Runs continuous AI-based order queue optimization.
        """
        logging.info("🚀 AI Order Queue Optimization Running...")
        while True:
            await self.adjust_order_queue()
            await asyncio.sleep(1)

# Example Usage
if __name__ == "__main__":
    optimizer = OrderQueueOptimizer()
    asyncio.run(optimizer.optimize_order_execution())
