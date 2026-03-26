"""Feature extraction léger pour reconnaissance individuelle."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image


class FeatureExtractor:
    """Extrait un embedding compact (histogrammes couleur + luminance)."""

    def __init__(self, bins: int = 16):
        self.bins = bins

    def extract(self, image_path: str, bbox: tuple[int, int, int, int] | None = None) -> list[float]:
        image = Image.open(image_path).convert("RGB")
        if bbox is not None:
            x1, y1, x2, y2 = bbox
            x1 = max(0, int(x1))
            y1 = max(0, int(y1))
            x2 = min(image.width, int(x2))
            y2 = min(image.height, int(y2))
            if x2 > x1 and y2 > y1:
                image = image.crop((x1, y1, x2, y2))

        image = image.resize((96, 96), Image.BILINEAR)

        r_hist = image.getchannel("R").histogram()
        g_hist = image.getchannel("G").histogram()
        b_hist = image.getchannel("B").histogram()
        gray_hist = image.convert("L").histogram()

        embedding = []
        step = 256 // self.bins
        for start in range(0, 256, step):
            end = start + step
            embedding.append(sum(r_hist[start:end]))
            embedding.append(sum(g_hist[start:end]))
            embedding.append(sum(b_hist[start:end]))
            embedding.append(sum(gray_hist[start:end]))

        return self._l2_normalize(embedding)

    @staticmethod
    def _l2_normalize(vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(v * v for v in vector))
        if norm <= 1e-12:
            return [0.0 for _ in vector]
        return [v / norm for v in vector]
