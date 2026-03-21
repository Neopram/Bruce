import aiosqlite
import logging
from typing import List, Dict, Any, Optional

# Logger configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Database Configuration
DATABASE_PATH = "trading_bot.db"


class DatabaseManager:
    """
    Asynchronous database manager for handling trade data efficiently.
    """

    def __init__(self, db_path: str = DATABASE_PATH):
        """
        Initializes the database manager.

        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path

    async def connect(self):
        """
        Establishes an asynchronous connection to the database.

        Returns:
            aiosqlite.Connection: Database connection.
        """
        try:
            connection = await aiosqlite.connect(self.db_path)
            connection.row_factory = aiosqlite.Row  # Enables dictionary-like access
            logging.info(f"✅ Connected to database at {self.db_path}")
            return connection
        except Exception as e:
            logging.error(f"🚨 Database connection failed: {e}")
            return None

    async def initialize_database(self):
        """
        Initializes the database with necessary tables and indexes.
        """
        async with await self.connect() as db:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trading_pair TEXT NOT NULL,
                    action TEXT NOT NULL CHECK(action IN ('BUY', 'SELL')),
                    price REAL NOT NULL,
                    volume REAL NOT NULL,
                    timestamp TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_trading_pair ON trades(trading_pair);
                CREATE INDEX IF NOT EXISTS idx_timestamp ON trades(timestamp);
            """)
            await db.commit()
            logging.info("📂 Database initialized with tables and indexes.")

    async def insert_trade(self, trade_data: Dict[str, Any]):
        """
        Inserts a trade record asynchronously.

        Args:
            trade_data (Dict[str, Any]): Trade data dictionary.
        """
        query = """
            INSERT INTO trades (trading_pair, action, price, volume, timestamp)
            VALUES (:trading_pair, :action, :price, :volume, :timestamp);
        """
        async with await self.connect() as db:
            await db.execute(query, trade_data)
            await db.commit()
            logging.info(f"✅ Trade inserted: {trade_data}")

    async def batch_insert_trades(self, trades: List[Dict[str, Any]]):
        """
        Inserts multiple trades at once for efficiency.

        Args:
            trades (List[Dict[str, Any]]): List of trade dictionaries.
        """
        query = """
            INSERT INTO trades (trading_pair, action, price, volume, timestamp)
            VALUES (?, ?, ?, ?, ?);
        """
        values = [(t["trading_pair"], t["action"], t["price"], t["volume"], t["timestamp"]) for t in trades]

        async with await self.connect() as db:
            await db.executemany(query, values)
            await db.commit()
            logging.info(f"📊 Batch inserted {len(trades)} trades.")

    async def query_trades(self, trading_pair: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Queries trades by trading pair with an optional limit.

        Args:
            trading_pair (str): Trading pair to query.
            limit (int): Maximum number of results to return.

        Returns:
            List[Dict[str, Any]]: List of trade records.
        """
        query = """
            SELECT * FROM trades WHERE trading_pair = ? ORDER BY timestamp DESC LIMIT ?;
        """
        async with await self.connect() as db:
            async with db.execute(query, (trading_pair, limit)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def update_trade(self, trade_id: int, price: float, volume: float):
        """
        Updates an existing trade record.

        Args:
            trade_id (int): Trade ID.
            price (float): Updated price.
            volume (float): Updated volume.
        """
        query = """
            UPDATE trades SET price = ?, volume = ? WHERE trade_id = ?;
        """
        async with await self.connect() as db:
            await db.execute(query, (price, volume, trade_id))
            await db.commit()
            logging.info(f"✅ Trade {trade_id} updated.")

    async def delete_trade(self, trade_id: int):
        """
        Deletes a trade record by ID.

        Args:
            trade_id (int): Trade ID.
        """
        query = """
            DELETE FROM trades WHERE trade_id = ?;
        """
        async with await self.connect() as db:
            await db.execute(query, (trade_id,))
            await db.commit()
            logging.info(f"🗑️ Trade {trade_id} deleted.")

    async def execute_query(self, query: str, params: Optional[List[Any]] = None):
        """
        Executes a query without returning results.

        Args:
            query (str): SQL query.
            params (Optional[List[Any]]): Query parameters.
        """
        async with await self.connect() as db:
            await db.execute(query, params or [])
            await db.commit()
            logging.info(f"🔄 Executed query: {query}")

    async def fetch_all(self, query: str, params: Optional[List[Any]] = None) -> List[Any]:
        """
        Executes a SELECT query and returns all results.

        Args:
            query (str): SQL query.
            params (Optional[List[Any]]): Query parameters.

        Returns:
            List[Any]: Query results.
        """
        async with await self.connect() as db:
            async with db.execute(query, params or []) as cursor:
                rows = await cursor.fetchall()
                logging.info(f"📊 Retrieved {len(rows)} rows.")
                return rows

# Example Usage
async def main():
    db_manager = DatabaseManager()

    await db_manager.initialize_database()
    await db_manager.insert_trade({
        "trading_pair": "BTC/USDT",
        "action": "BUY",
        "price": 45000.0,
        "volume": 1.5,
        "timestamp": "2025-01-20 12:00:00"
    })

    trades = await db_manager.query_trades("BTC/USDT", limit=5)
    print("📈 Recent Trades:", trades)

    await db_manager.update_trade(trades[0]['trade_id'], price=45500.0, volume=2.0)
    await db_manager.delete_trade(trades[0]['trade_id'])

# Run Example
if __name__ == "__main__":
    asyncio.run(main())
