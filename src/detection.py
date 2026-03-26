"""
Point d'entrée de la future détection d'oiseaux.
"""
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BirdDetection:
    label: str
    confidence: float
    bbox: tuple[int, int, int, int] | None = None


class BirdDetector:
    """Stub de détection appelé uniquement après détection de mouvement."""

    def detect(self, image_path: str):
        logger.info("Bird detection placeholder triggered for %s", image_path)
        return []