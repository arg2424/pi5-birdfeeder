"""
Entry point - Placeholder pour Phase 1.
"""
import logging
import os
import time
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer config
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from camera import CameraHandler
from config import CAPTURE_INTERVAL_SECONDS, LOG_FILE, LOG_LEVEL
from database import DatabaseHandler
from detection import BirdDetector
from motion import MotionDetector

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
                    database.record_motion_event(
                        image_path=persisted_image_path,
                        motion_score=motion_result.score,
                        threshold=motion_result.threshold,
                        bird_detections=len(detections),
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
