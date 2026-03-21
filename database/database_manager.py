import asyncpg
import logging
from typing import Dict, Any

class DatabaseManager:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool = None

    async def initialize_database(self):
        """
        Initializes the database connection pool asynchronously.
        """
        try:
            self.pool = await asyncpg.create_pool(self.connection_string, min_size=1, max_size=5)
            logging.info("✅ Database connection pool initialized successfully.")
        except Exception as e:
            logging.error(f"❌ Database initialization failed: {str(e)}")

    async def close_connection(self):
        """
        Closes the database connection pool.
        """
        if self.pool:
            await self.pool.close()
            logging.info("🔴 Database connection pool closed.")

    async def insert_trade(self, trade_data: Dict[str, Any]):
        """
        Inserts a trade into the database.
        """
        query = """
        INSERT INTO trades (trade_id, symbol, quantity, price)
        VALUES ($1, $2, $3, $4)
        RETURNING trade_id;
        """
        try:
            async with self.pool.acquire() as connection:
                trade_id = await connection.fetchval(query, trade_data['trade_id'], trade_data['symbol'], trade_data['quantity'], trade_data['price'])
                logging.info(f"✅ Trade inserted: {trade_id}")
                return trade_id
        except Exception as e:
            logging.error(f"❌ Trade insertion failed: {str(e)}")
            return None

    async def update_trade(self, trade_data: Dict[str, Any]):
        """
        Updates a trade in the database.
        """
        query = """
        UPDATE trades SET quantity = $2, price = $3 WHERE trade_id = $1;
        """
        try:
            async with self.pool.acquire() as connection:
                await connection.execute(query, trade_data['trade_id'], trade_data['quantity'], trade_data['price'])
                logging.info(f"✅ Trade updated: {trade_data['trade_id']}")
        except Exception as e:
            logging.error(f"❌ Trade update failed: {str(e)}")

    async def query_trade(self, trade_id: int):
        """
        Queries a trade by trade_id.
        """
        query = """
        SELECT * FROM trades WHERE trade_id = $1;
        """
        try:
            async with self.pool.acquire() as connection:
                trade = await connection.fetchrow(query, trade_id)
                if trade:
                    logging.info(f"🔍 Trade found: {trade_id}")
                    return dict(trade)
                else:
                    logging.warning(f"⚠️ No trade found for ID: {trade_id}")
                    return None
        except Exception as e:
            logging.error(f"❌ Trade query failed: {str(e)}")
            return None
