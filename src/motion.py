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
    MOTION_ARM_CONSECUTIVE,
    MOTION_RESIZE_HEIGHT,
    MOTION_RESIZE_WIDTH,
    MOTION_SCORE_SMOOTHING,
    MOTION_SCORE_THRESHOLD,
)

logger = logging.getLogger(__name__)


@dataclass
class MotionResult:
    detected: bool
    score: float
    raw_score: float
    threshold: float
    consecutive_hits: int


class MotionDetector:
    """Détecteur de mouvement basé sur la différence moyenne entre images."""

    def __init__(self):
        self.threshold = MOTION_SCORE_THRESHOLD
        self.analysis_size = (MOTION_RESIZE_WIDTH, MOTION_RESIZE_HEIGHT)
        self.smoothing = min(0.99, max(0.0, MOTION_SCORE_SMOOTHING))
        self.arm_consecutive = max(1, MOTION_ARM_CONSECUTIVE)
        self._smoothed_score: float | None = None
        self._consecutive_hits = 0

    def _prepare_image(self, image_path: str) -> Image.Image:
        with Image.open(image_path) as image:
            return image.convert("L").resize(self.analysis_size)

    def compare(self, previous_image_path: str, current_image_path: str) -> MotionResult:
        previous = self._prepare_image(previous_image_path)
        current = self._prepare_image(current_image_path)

        diff = ImageChops.difference(previous, current)
        raw_score = ImageStat.Stat(diff).mean[0] / 255.0
        if self._smoothed_score is None:
            self._smoothed_score = raw_score
        else:
            self._smoothed_score = (self.smoothing * raw_score) + ((1.0 - self.smoothing) * self._smoothed_score)

        score = self._smoothed_score
        if score >= self.threshold:
            self._consecutive_hits += 1
        else:
            self._consecutive_hits = 0

        detected = self._consecutive_hits >= self.arm_consecutive

        logger.info(
            "Motion analysis: raw=%.4f smoothed=%.4f threshold=%.4f hits=%d detected=%s",
            raw_score,
            score,
            self.threshold,
            self._consecutive_hits,
            detected,
        )

        return MotionResult(
            detected=detected,
            score=score,
            raw_score=raw_score,
            threshold=self.threshold,
            consecutive_hits=self._consecutive_hits,
        )