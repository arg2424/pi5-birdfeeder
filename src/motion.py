"""
Détection simple de mouvement par différence entre deux captures.
"""
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from config import (
    MOTION_RESIZE_HEIGHT,
    MOTION_RESIZE_WIDTH,
    MOTION_SCORE_THRESHOLD,
)

logger = logging.getLogger(__name__)


@dataclass
class MotionResult:
    detected: bool
    score: float
    threshold: float


class MotionDetector:
    """Détecteur de mouvement basé sur la différence moyenne entre images."""

    def __init__(self):
        self.threshold = MOTION_SCORE_THRESHOLD
        self.analysis_size = (MOTION_RESIZE_WIDTH, MOTION_RESIZE_HEIGHT)

    def _prepare_image(self, image_path: str) -> Image.Image:
        with Image.open(image_path) as image:
            return image.convert("L").resize(self.analysis_size)

    def compare(self, previous_image_path: str, current_image_path: str) -> MotionResult:
        previous = self._prepare_image(previous_image_path)
        current = self._prepare_image(current_image_path)

        diff = ImageChops.difference(previous, current)
        score = ImageStat.Stat(diff).mean[0] / 255.0
        detected = score >= self.threshold

        logger.info(
            "Motion analysis: score=%.4f threshold=%.4f detected=%s",
            score,
            self.threshold,
            detected,
        )

        return MotionResult(
            detected=detected,
            score=score,
            threshold=self.threshold,
        )