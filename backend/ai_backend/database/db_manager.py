"""
Database Manager
Handles TinyDB connections and table management
"""

from pathlib import Path
from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
from typing import Optional


class DatabaseManager:
    """
    Manages TinyDB database connections and provides access to tables.
    Singleton pattern to ensure single database instance.
    """

    _instance: Optional['DatabaseManager'] = None
    _db: Optional[TinyDB] = None

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database manager

        Args:
            db_path: Path to database file (defaults to ai_backend/database/data.json)
        """
        if self._db is None:
            if db_path is None:
                # Default path: ai_backend/database/data.json
                db_path = Path(__file__).parent / "data.json"
            else:
                db_path = Path(db_path)

            # Create directory if it doesn't exist
            db_path.parent.mkdir(parents=True, exist_ok=True)

            # Initialize TinyDB with caching middleware for performance
            self._db = TinyDB(
                db_path,
                storage=CachingMiddleware(JSONStorage),
                indent=2,
                ensure_ascii=False
            )

            self.db_path = db_path
            print(f"Database initialized at: {db_path}")

    @property
    def db(self) -> TinyDB:
        """Get database instance"""
        if self._db is None:
            raise RuntimeError("Database not initialized")
        return self._db

    def get_table(self, table_name: str):
        """
        Get or create a table

        Args:
            table_name: Name of the table

        Returns:
            TinyDB Table instance
        """
        return self.db.table(table_name)

    def list_tables(self) -> list:
        """List all tables in the database"""
        return self.db.tables()

    def drop_table(self, table_name: str):
        """
        Drop a table

        Args:
            table_name: Name of the table to drop
        """
        self.db.drop_table(table_name)
        print(f"Dropped table: {table_name}")

    def close(self):
        """Close database connection"""
        if self._db is not None:
            self._db.close()
            self._db = None
            print("Database connection closed")

    def get_stats(self) -> dict:
        """
        Get database statistics

        Returns:
            Dictionary with database stats
        """
        stats = {
            "db_path": str(self.db_path),
            "tables": {},
            "total_documents": 0
        }

        for table_name in self.db.tables():
            table = self.get_table(table_name)
            count = len(table)
            stats["tables"][table_name] = count
            stats["total_documents"] += count

        return stats
