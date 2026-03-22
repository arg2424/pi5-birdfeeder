"""
Module base de données SQLite - Phase 1.
"""
import logging
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_PATH

logger = logging.getLogger(__name__)

class DatabaseHandler:
    """Gestionnaire de base de données SQLite."""
    
    def __init__(self):
        self.db_path = DB_PATH
        logger.info(f"🗄️  Database: {self.db_path}")
    
    def init_schema(self):
        """Initialiser le schéma (Phase 3)"""
        # TODO: implement schema creation
        logger.info("Schema initialization (Phase 3 TODO)")

if __name__ == "__main__":
    db = DatabaseHandler()
