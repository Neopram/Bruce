import sqlite3
import logging
from typing import List, Any, Optional

# Logger configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class DatabaseManager:
    """
    A utility class to manage SQLite database operations.
    """
    def __init__(self, db_path: str):
        """
        Initializes the database manager with a connection to the specified database.

        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path
        self.connection = None
        self.cursor = None

    def connect(self):
        """
        Establishes a connection to the database.
        """
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.cursor = self.connection.cursor()
            logging.info(f"Connected to database at {self.db_path}")
        except sqlite3.Error as e:
            logging.error(f"Failed to connect to database: {e}")
            raise

    def initialize_database(self):
        """
        Initializes the database by creating necessary tables.
        """
        self.connect()
        self.create_tables()

    def create_tables(self):
        """
        Creates necessary tables in the database.
        """
        with self.connection:
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id INTEGER PRIMARY KEY,
                    trading_pair TEXT NOT NULL,
                    action TEXT NOT NULL,
                    price REAL NOT NULL,
                    volume REAL NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
        logging.info("Tables created successfully.")

    def close_connection(self):
        """
        Closes the database connection.
        """
        try:
            if self.connection:
                self.connection.close()
                logging.info("Database connection closed.")
        except sqlite3.Error as e:
            logging.error(f"Failed to close the database connection: {e}")

    def insert_trade(self, trade_data):
        """
        Inserts a trade record into the database.

        Args:
            trade_data (dict): Trade data to insert.
        """
        with self.connection:
            self.connection.execute("""
                INSERT INTO trades (trade_id, trading_pair, action, price, volume, timestamp)
                VALUES (:trade_id, :trading_pair, :action, :price, :volume, :timestamp)
            """, trade_data)
        logging.info("Trade inserted successfully.")

    def query_trades(self, trading_pair):
        """
        Queries trades from the database by trading pair.

        Args:
            trading_pair (str): Trading pair to query.

        Returns:
            List[dict]: List of trade records.
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM trades WHERE trading_pair = ?
        """, (trading_pair,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def update_trade(self, trade_data):
        """
        Updates a trade record in the database.

        Args:
            trade_data (dict): Trade data to update.
        """
        with self.connection:
            self.connection.execute("""
                UPDATE trades
                SET price = :price, volume = :volume
                WHERE trade_id = :trade_id
            """, trade_data)
        logging.info("Trade updated successfully.")

    def delete_trade(self, trade_id):
        """
        Deletes a trade record from the database.

        Args:
            trade_id (int): Trade ID to delete.
        """
        with self.connection:
            self.connection.execute("""
                DELETE FROM trades WHERE trade_id = ?
            """, (trade_id,))
        logging.info("Trade deleted successfully.")

    def execute_query(self, query: str, params: Optional[List[Any]] = None) -> None:
        """
        Executes a query without returning results (e.g., INSERT, UPDATE).

        Args:
            query (str): The SQL query to execute.
            params (Optional[List[Any]]): Parameters for the query.
        """
        try:
            if not self.connection:
                self.connect()
            self.cursor.execute(query, params or [])
            self.connection.commit()
            logging.info(f"Executed query: {query}")
        except sqlite3.Error as e:
            logging.error(f"Failed to execute query: {e}")
            raise

    def fetch_all(self, query: str, params: Optional[List[Any]] = None) -> List[Any]:
        """
        Executes a SELECT query and returns all results.

        Args:
            query (str): The SQL query to execute.
            params (Optional[List[Any]]): Parameters for the query.

        Returns:
            List[Any]: Results of the query.
        """
        try:
            if not self.connection:
                self.connect()
            self.cursor.execute(query, params or [])
            results = self.cursor.fetchall()
            logging.info(f"Fetched {len(results)} rows from query: {query}")
            return results
        except sqlite3.Error as e:
            logging.error(f"Failed to fetch data: {e}")
            raise

    def close(self):
        """
        Closes the database connection.
        """
        try:
            if self.connection:
                self.connection.close()
                logging.info("Database connection closed.")
        except sqlite3.Error as e:
            logging.error(f"Failed to close the database connection: {e}")

# Example usage
if __name__ == "__main__":
    db_manager = DatabaseManager("trading_bot.db")
    try:
        db_manager.connect()
        db_manager.execute_query("CREATE TABLE IF NOT EXISTS trades (id INTEGER PRIMARY KEY, price REAL, volume REAL, timestamp TEXT)")
        db_manager.execute_query("INSERT INTO trades (price, volume, timestamp) VALUES (?, ?, ?)", [100.5, 10, "2025-01-20 12:00:00"])
        trades = db_manager.fetch_all("SELECT * FROM trades")
        print("Trades:", trades)
    finally:
        db_manager.close()