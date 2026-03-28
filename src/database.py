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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS individuals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    sightings_count INTEGER NOT NULL DEFAULT 0,
                    prototype_embedding TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sightings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    image_path TEXT NOT NULL,
                    crop_path TEXT,
                    individual_id INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    motion_event_id INTEGER,
                    bbox_x1 INTEGER,
                    bbox_y1 INTEGER,
                    bbox_x2 INTEGER,
                    bbox_y2 INTEGER,
                    FOREIGN KEY(individual_id) REFERENCES individuals(id),
                    FOREIGN KEY(motion_event_id) REFERENCES motion_events(id)
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
    ) -> int:
        """Enregistrer un événement de mouvement pour audit et tests."""
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
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
        return int(cursor.lastrowid)

    def get_individual_embeddings(self) -> list[tuple[int, list[float]]]:
        """Retourne les embeddings prototypes des individus connus."""
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT id, prototype_embedding
                FROM individuals
                ORDER BY id ASC
                """
            ).fetchall()
        result = []
        for row in rows:
            individual_id, serialized = row
            embedding = [float(x) for x in serialized.split(",") if x]
            result.append((int(individual_id), embedding))
        return result

    def create_individual(self, embedding: list[float]) -> int:
        """Créer un nouvel individu avec embedding prototype."""
        now = datetime.utcnow().isoformat(timespec="seconds")
        serialized = ",".join(f"{x:.8f}" for x in embedding)
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO individuals (
                    created_at,
                    last_seen_at,
                    sightings_count,
                    prototype_embedding
                ) VALUES (?, ?, ?, ?)
                """,
                (now, now, 1, serialized),
            )
            connection.commit()
        return int(cursor.lastrowid)

    def update_individual_seen(self, individual_id: int) -> None:
        """Met à jour la date de dernière observation et le compteur."""
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                UPDATE individuals
                SET last_seen_at = ?, sightings_count = sightings_count + 1
                WHERE id = ?
                """,
                (datetime.utcnow().isoformat(timespec="seconds"), individual_id),
            )
            connection.commit()

    def record_sighting(
        self,
        image_path: str,
        individual_id: int,
        confidence: float,
        bbox: tuple[int, int, int, int] | None,
        motion_event_id: int | None,
        crop_path: str | None = None,
    ) -> int:
        """Enregistre une observation d'oiseau associée à un individu."""
        x1 = y1 = x2 = y2 = None
        if bbox is not None:
            x1, y1, x2, y2 = bbox
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO sightings (
                    created_at,
                    image_path,
                    crop_path,
                    individual_id,
                    confidence,
                    motion_event_id,
                    bbox_x1,
                    bbox_y1,
                    bbox_x2,
                    bbox_y2
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.utcnow().isoformat(timespec="seconds"),
                    image_path,
                    crop_path,
                    individual_id,
                    confidence,
                    motion_event_id,
                    x1,
                    y1,
                    x2,
                    y2,
                ),
            )
            connection.commit()
        return int(cursor.lastrowid)

    def reset_all(self) -> None:
        """Remet à zéro toutes les tables (conserve le schéma)."""
        with sqlite3.connect(self.db_path) as connection:
            connection.execute("DELETE FROM sightings")
            connection.execute("DELETE FROM individuals")
            connection.execute("DELETE FROM motion_events")
            connection.execute("DELETE FROM sqlite_sequence WHERE name IN ('sightings','individuals','motion_events')")
            connection.commit()
        logger.info("Database reset: all tables cleared")

if __name__ == "__main__":
    db = DatabaseHandler()
