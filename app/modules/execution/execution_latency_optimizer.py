import logging
import time
import asyncio
import numpy as np
from statistics import mean
from app.modules.websocket.websocket_client import OKXWebSocketClient
from app.modules.order_manager import OrderManager

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
LATENCY_THRESHOLD = 5  # Acceptable execution latency in milliseconds
SPEED_BOOST_FACTOR = 1.2  # AI-driven execution speed adjustment factor
EXCHANGE_LATENCY_HISTORY = {}  # Stores latency history per exchange
EXCHANGES = ["OKX", "Binance", "Coinbase", "FTX"]  # Monitored exchanges

class ExecutionLatencyOptimizer:
    """
    AI-Driven Execution Latency Optimization Engine.
    """

    def __init__(self):
        """
        Initializes the execution latency optimizer.
        """
        self.websocket = OKXWebSocketClient()
        self.order_manager = OrderManager()

    def measure_latency(self):
        """
        Measures trade execution latency.
        
        Returns:
            float: Execution latency in milliseconds.
        """
        start_time = time.time()
        time.sleep(np.random.uniform(0.001, 0.010))  # Simulated latency measurement
        latency = (time.time() - start_time) * 1000  # Convert to milliseconds
        return latency

    async def track_exchange_latency(self, exchange):
        """
        Tracks and logs latency per exchange.

        Args:
            exchange (str): Exchange name.
        """
        latency = self.measure_latency()

        if exchange not in EXCHANGE_LATENCY_HISTORY:
            EXCHANGE_LATENCY_HISTORY[exchange] = []

        EXCHANGE_LATENCY_HISTORY[exchange].append(latency)
        EXCHANGE_LATENCY_HISTORY[exchange] = EXCHANGE_LATENCY_HISTORY[exchange][-10:]  # Keep last 10 records

        logging.info(f"📡 Measured Latency for {exchange}: {latency:.2f} ms")

    async def select_fastest_exchange(self):
        """
        Selects the fastest exchange for trade execution.
        
        Returns:
            str: Best exchange with lowest latency.
        """
        latencies = {
            exchange: mean(EXCHANGE_LATENCY_HISTORY.get(exchange, [LATENCY_THRESHOLD])) 
            for exchange in EXCHANGES
        }
        best_exchange = min(latencies, key=latencies.get)

        logging.info(f"⚡ Fastest Exchange Selected: {best_exchange} ({latencies[best_exchange]:.2f} ms)")
        return best_exchange

    def adjust_execution_speed(self, current_latency):
        """
        Adjusts execution speed based on real-time latency.
        
        Args:
            current_latency (float): Measured execution latency in milliseconds.
            
        Returns:
            float: Optimized execution speed adjustment factor.
        """
        if current_latency > LATENCY_THRESHOLD:
            return SPEED_BOOST_FACTOR
        return 1.0

    async def optimize_execution_latency(self):
        """
        Continuously optimizes trade execution for low latency.
        """
        logging.info("🚀 AI Execution Latency Optimizer Running...")

        while True:
            for exchange in EXCHANGES:
                await self.track_exchange_latency(exchange)

            best_exchange = await self.select_fastest_exchange()
            await self.order_manager.update_best_execution_route(best_exchange)

            latency = self.measure_latency()
            adjustment_factor = self.adjust_execution_speed(latency)

            logging.info(f"⚡ Execution Latency: {latency:.2f} ms | Adjusting Speed by {adjustment_factor:.2f}x")

            await asyncio.sleep(5)  # Runs optimization every 5 seconds

# Example Usage
if __name__ == "__main__":
    optimizer = ExecutionLatencyOptimizer()
    asyncio.run(optimizer.optimize_execution_latency())
