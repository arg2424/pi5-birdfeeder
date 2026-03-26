"""
Détection d'oiseaux via YOLO11n ONNX (classes COCO, classe 14 = bird).
"""
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.append(str(Path(__file__).parent.parent))
from config import YOLO_MODEL, YOLO_CONFIDENCE, YOLO_IOU

logger = logging.getLogger(__name__)

COCO_BIRD_CLASS = 14
YOLO_INPUT_SIZE = 640


@dataclass
class BirdDetection:
    label: str
    confidence: float
    bbox: tuple[int, int, int, int] | None = None


def _letterbox(img: Image.Image, size: int = YOLO_INPUT_SIZE):
    """Resize avec letterbox (padding gris 114) → carré size×size."""
    orig_w, orig_h = img.size
    scale = min(size / orig_w, size / orig_h)
    new_w, new_h = int(orig_w * scale), int(orig_h * scale)
    resized = img.resize((new_w, new_h), Image.BILINEAR)
    pad_x = (size - new_w) // 2
    pad_y = (size - new_h) // 2
    padded = Image.new("RGB", (size, size), (114, 114, 114))
    padded.paste(resized, (pad_x, pad_y))
    arr = np.array(padded, dtype=np.float32) / 255.0
    arr = arr.transpose(2, 0, 1)[np.newaxis]  # HWC → 1,C,H,W
    return arr, scale, pad_x, pad_y


def _nms(x1, y1, x2, y2, scores, iou_threshold: float):
    """NMS simple sur tableau numpy, retourne indices retenus."""
    indices = np.argsort(scores)[::-1]
    kept = []
    while len(indices) > 0:
        i = indices[0]
        kept.append(i)
        if len(indices) == 1:
            break
        rest = indices[1:]
        ix1 = np.maximum(x1[i], x1[rest])
        iy1 = np.maximum(y1[i], y1[rest])
        ix2 = np.minimum(x2[i], x2[rest])
        iy2 = np.minimum(y2[i], y2[rest])
        inter = np.maximum(0.0, ix2 - ix1) * np.maximum(0.0, iy2 - iy1)
        area_i = (x2[i] - x1[i]) * (y2[i] - y1[i])
        area_rest = (x2[rest] - x1[rest]) * (y2[rest] - y1[rest])
        iou = inter / (area_i + area_rest - inter + 1e-6)
        indices = rest[iou < iou_threshold]
    return kept


class BirdDetector:
    """Détection d'oiseaux YOLO11n via ONNX Runtime."""

    def __init__(self):
        model_path = str(YOLO_MODEL)
        if not Path(model_path).exists():
            logger.warning("Modèle ONNX introuvable: %s — détection désactivée", model_path)
            self._session = None
            return
        try:
            import onnxruntime as ort
            self._session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
            self._input_name = self._session.get_inputs()[0].name
            logger.info("🦅 BirdDetector chargé: %s", Path(model_path).name)
        except Exception as exc:
            logger.error("Erreur chargement ONNX: %s", exc)
            self._session = None

    def detect(self, image_path: str) -> list[BirdDetection]:
        if self._session is None:
            return []

        img = Image.open(image_path).convert("RGB")
        orig_w, orig_h = img.size
        tensor, scale, pad_x, pad_y = _letterbox(img)

        raw = self._session.run(None, {self._input_name: tensor})[0]
        # raw shape: [1, 84, 8400]  (4 bbox + 80 classes)
        preds = raw[0].T  # → [8400, 84]

        bird_scores = preds[:, 4 + COCO_BIRD_CLASS]
        mask = bird_scores >= YOLO_CONFIDENCE
        if not mask.any():
            logger.info("No bird detected in %s", Path(image_path).name)
            return []

        boxes = preds[mask, :4]
        scores = bird_scores[mask]

        # cx,cy,w,h → x1,y1,x2,y2 dans l'espace 640×640
        x1 = boxes[:, 0] - boxes[:, 2] / 2
        y1 = boxes[:, 1] - boxes[:, 3] / 2
        x2 = boxes[:, 0] + boxes[:, 2] / 2
        y2 = boxes[:, 1] + boxes[:, 3] / 2

        # Retirer padding et ramener aux coords originales
        x1 = np.clip((x1 - pad_x) / scale, 0, orig_w)
        y1 = np.clip((y1 - pad_y) / scale, 0, orig_h)
        x2 = np.clip((x2 - pad_x) / scale, 0, orig_w)
        y2 = np.clip((y2 - pad_y) / scale, 0, orig_h)

        kept = _nms(x1, y1, x2, y2, scores, YOLO_IOU)
        detections = [
            BirdDetection(
                label="bird",
                confidence=float(scores[i]),
                bbox=(int(x1[i]), int(y1[i]), int(x2[i]), int(y2[i])),
            )
            for i in kept
        ]
        logger.info(
            "🐦 %d bird(s) detected in %s (conf≥%.2f)",
            len(detections), Path(image_path).name, YOLO_CONFIDENCE,
        )
        return detections