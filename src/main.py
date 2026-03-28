"""
Entry point - Placeholder pour Phase 1.
"""
import logging
import os
import time
import sys
from datetime import datetime
from pathlib import Path

# Ajouter le répertoire parent au path pour importer config
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from camera import CameraHandler
from config import CAPTURE_INTERVAL_SECONDS, EMBEDDING_THRESHOLD, LOG_FILE, LOG_LEVEL, MAX_INDIVIDUALS, MESANGE_DIR
from database import DatabaseHandler
from detection import BirdDetector
from features import FeatureExtractor
from matching import IndividualMatcher
from motion import MotionDetector
from PIL import Image

# Setup logging
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("🐦 Pi5 Bird Feeder - Starting...")
    logger.info("Phase 1: Setup & Camera Capture")
    logger.info("Capture interval: %ss", CAPTURE_INTERVAL_SECONDS)

    camera = CameraHandler()
    database = DatabaseHandler()
    bird_detector = BirdDetector()
    feature_extractor = FeatureExtractor()
    matcher = IndividualMatcher(threshold=EMBEDDING_THRESHOLD)
    motion_detector = MotionDetector()
    previous_image_path = None

    camera.cleanup_staging()
    database.init_schema()
    print("✅ Camera loop started. Ctrl+C pour arrêter.")

    try:
        while True:
            image_path = camera.capture_staging_image()
            logger.info("Staging image saved: %s", image_path)

            if previous_image_path is not None:
                motion_result = motion_detector.compare(previous_image_path, image_path)
                if motion_result.detected:
                    persisted_image_path = camera.persist_image(image_path)
                    detections = bird_detector.detect(persisted_image_path)
                    motion_event_id = database.record_motion_event(
                        image_path=persisted_image_path,
                        motion_score=motion_result.score,
                        threshold=motion_result.threshold,
                        bird_detections=len(detections),
                    )

                    if detections:
                        candidates = database.get_individual_embeddings()
                        for det_idx, detection in enumerate(detections):
                            embedding = feature_extractor.extract(
                                persisted_image_path,
                                bbox=detection.bbox,
                            )
                            match = matcher.match(embedding, candidates)

                            if match is None:
                                if len(candidates) < MAX_INDIVIDUALS:
                                    individual_id = database.create_individual(embedding)
                                    candidates.append((individual_id, embedding))
                                    score = 1.0
                                    logger.info("New individual created: #%d", individual_id)
                                else:
                                    logger.warning(
                                        "Max individuals reached (%d), sighting ignored",
                                        MAX_INDIVIDUALS,
                                    )
                                    continue
                            else:
                                individual_id, score = match
                                database.update_individual_seen(individual_id)

                            # --- Save crop to data/mesange/ ---
                            crop_path = None
                            try:
                                img = Image.open(persisted_image_path)
                                x1, y1, x2, y2 = detection.bbox
                                crop = img.crop((x1, y1, x2, y2))
                                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                                crop_filename = f"mesange_{ts}_indiv{individual_id}_{det_idx}.jpg"
                                crop_dest = MESANGE_DIR / crop_filename
                                crop.save(str(crop_dest), format="JPEG", quality=90)
                                crop_path = str(crop_dest)
                                logger.info("Crop saved: %s", crop_dest)
                            except Exception as exc:
                                logger.warning("Crop save failed: %s", exc)

                            database.record_sighting(
                                image_path=persisted_image_path,
                                individual_id=individual_id,
                                confidence=detection.confidence,
                                bbox=detection.bbox,
                                motion_event_id=motion_event_id,
                                crop_path=crop_path,
                            )
                            logger.info(
                                "Bird sighting linked to individual #%d (similarity=%.3f, conf=%.3f)",
                                individual_id,
                                score,
                                detection.confidence,
                            )

                    logger.info("Motion detected before bird detection: score=%.4f", motion_result.score)
                else:
                    logger.info("No significant motion: score=%.4f", motion_result.score)

                if previous_image_path != image_path and Path(previous_image_path).parent.name == "staging":
                    try:
                        os.remove(previous_image_path)
                    except FileNotFoundError:
                        pass

            previous_image_path = image_path
            time.sleep(CAPTURE_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        logger.info("Arrêt demandé par l'utilisateur")
    finally:
        camera.close()
        logger.info("Pi5 Bird Feeder stopped")

if __name__ == "__main__":
    main()
