"""
Module base de données SQLite - Phase 1.
"""
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from config import DB_PATH

logger = logging.getLogger(__name__)

class DatabaseHandler:
    """Gestionnaire de base de données SQLite."""
    
    def __init__(self):
        self.db_path = DB_PATH
        logger.info(f"🗄️  Database: {self.db_path}")
    
    def init_schema(self):
        """Initialiser le schéma minimal utilisé dès la Phase 1."""
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS motion_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    image_path TEXT NOT NULL,
                    motion_score REAL NOT NULL,
                    threshold REAL NOT NULL,
                    bird_detections INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            connection.commit()
        logger.info("Schema initialized")

    def record_motion_event(
        self,
        image_path: str,
        motion_score: float,
        threshold: float,
        bird_detections: int,
    ) -> None:
        """Enregistrer un événement de mouvement pour audit et tests."""
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO motion_events (
                    created_at,
                    image_path,
                    motion_score,
                    threshold,
                    bird_detections
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    datetime.utcnow().isoformat(timespec="seconds"),
                    image_path,
                    motion_score,
                    threshold,
                    bird_detections,
                ),
            )
            connection.commit()
        logger.info("Motion event recorded for %s", image_path)

if __name__ == "__main__":
    db = DatabaseHandler()
