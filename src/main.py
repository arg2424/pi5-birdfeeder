"""
Entry point - Placeholder pour Phase 1.
"""
import logging
import os
import time
import sys
from datetime import UTC, datetime
from pathlib import Path

# Ajouter le répertoire parent au path pour importer config
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from camera import CameraHandler
from config import (
    ALERT_MIN_CONFIDENCE,
    ALERT_NEW_INDIVIDUALS_ONLY,
    ALERT_WEBHOOK_URL,
    CAPTURE_INTERVAL_SECONDS,
    EMBEDDING_THRESHOLD,
    EVENT_RETENTION_DAYS,
    EVENT_CLIP_ENABLED,
    EVENT_CLIP_FRAME_INTERVAL_SECONDS,
    EVENT_CLIP_MAX_WIDTH,
    EVENT_CLIP_POST_FRAMES,
    EVENT_COOLDOWN_SECONDS,
    EVENTS_VIDEO_DIR,
    LOG_FILE,
    LOG_LEVEL,
    MAINTENANCE_INTERVAL_SECONDS,
    MAX_INDIVIDUALS,
    MESANGE_DIR,
    CAPTURES_DIR,
    SAVE_BIRD_EVENTS_ONLY,
)
from database import DatabaseHandler
from detection import BirdDetector
from features import FeatureExtractor
from matching import IndividualMatcher
from motion import MotionDetector
from PIL import Image

try:
    from .alerts import AlertSender
    from .maintenance import prune_old_files
except ImportError:
    from alerts import AlertSender
    from maintenance import prune_old_files

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


def _utc_now() -> datetime:
    return datetime.now(UTC)

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
    alert_sender = AlertSender(ALERT_WEBHOOK_URL)
    previous_image_path = None
    last_maintenance_at = 0.0

    camera.cleanup_staging()
    database.init_schema()
    print("✅ Camera loop started. Ctrl+C pour arrêter.")

    last_event_time: float = 0.0

    try:
        while True:
            image_path = camera.capture_staging_image()
            logger.info("Staging image saved: %s", image_path)

            if previous_image_path is not None:
                motion_result = motion_detector.compare(previous_image_path, image_path)
                if motion_result.detected:
                    now = time.time()
                    if EVENT_COOLDOWN_SECONDS > 0 and (now - last_event_time) < EVENT_COOLDOWN_SECONDS:
                        remaining = EVENT_COOLDOWN_SECONDS - (now - last_event_time)
                        logger.info("Motion suppressed by cooldown (%.1fs remaining)", remaining)
                    else:
                        last_event_time = now
                        persisted_image_path = camera.persist_image(image_path)
                        detections = bird_detector.detect(persisted_image_path)

                        if SAVE_BIRD_EVENTS_ONLY and not detections:
                            logger.info("No bird detected, event skipped (SAVE_BIRD_EVENTS_ONLY score=%.4f)", motion_result.score)
                            Path(persisted_image_path).unlink(missing_ok=True)
                        else:
                            motion_event_id = database.record_motion_event(
                                image_path=persisted_image_path,
                                motion_score=motion_result.score,
                                threshold=motion_result.threshold,
                                bird_detections=len(detections),
                            )

                            # Clip court (GIF) pour revue visuelle des événements.
                            if EVENT_CLIP_ENABLED:
                                clip_staging_paths = []
                                try:
                                    for _ in range(EVENT_CLIP_POST_FRAMES):
                                        time.sleep(EVENT_CLIP_FRAME_INTERVAL_SECONDS)
                                        clip_staging_paths.append(camera.capture_staging_image())

                                    frame_paths = [persisted_image_path, *clip_staging_paths]
                                    frames = []
                                    for frame_path in frame_paths:
                                        with Image.open(frame_path) as img_in:
                                            frame = img_in.convert("RGB")
                                            if EVENT_CLIP_MAX_WIDTH > 0 and frame.width > EVENT_CLIP_MAX_WIDTH:
                                                new_h = int(frame.height * EVENT_CLIP_MAX_WIDTH / frame.width)
                                                frame = frame.resize((EVENT_CLIP_MAX_WIDTH, new_h))
                                            frames.append(frame)

                                    if frames:
                                        clip_filename = f"event_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{motion_event_id}.gif"
                                        clip_dest = EVENTS_VIDEO_DIR / clip_filename
                                        duration_ms = max(40, int(EVENT_CLIP_FRAME_INTERVAL_SECONDS * 1000))
                                        frames[0].save(
                                            str(clip_dest),
                                            save_all=True,
                                            append_images=frames[1:],
                                            duration=duration_ms,
                                            loop=0,
                                        )
                                        database.set_motion_event_clip_path(motion_event_id, str(clip_dest))
                                        logger.info("Event clip saved: %s", clip_dest)
                                except Exception as exc:
                                    logger.warning("Event clip save failed: %s", exc)
                                finally:
                                    for clip_staging in clip_staging_paths:
                                        try:
                                            Path(clip_staging).unlink(missing_ok=True)
                                        except Exception:
                                            pass

                            if detections:
                                candidates = database.get_individual_embeddings()
                                for det_idx, detection in enumerate(detections):
                                    is_new_individual = False
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
                                            is_new_individual = True
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

                                    should_alert = detection.confidence >= ALERT_MIN_CONFIDENCE
                                    if ALERT_NEW_INDIVIDUALS_ONLY and not is_new_individual:
                                        should_alert = False
                                    if should_alert and alert_sender.enabled:
                                        alert_sender.send(
                                            title="bird_sighting",
                                            payload={
                                                "created_at": _utc_now().isoformat(timespec="seconds"),
                                                "individual_id": individual_id,
                                                "is_new_individual": is_new_individual,
                                                "confidence": round(float(detection.confidence), 4),
                                                "similarity": round(float(score), 4),
                                                "image_path": persisted_image_path,
                                                "crop_path": crop_path,
                                                "motion_event_id": motion_event_id,
                                            },
                                        )

                            logger.info("Motion event saved: score=%.4f bird_detections=%d", motion_result.score, len(detections))
                else:
                    logger.info("No significant motion: score=%.4f", motion_result.score)

                now = time.time()
                if MAINTENANCE_INTERVAL_SECONDS > 0 and (now - last_maintenance_at) >= MAINTENANCE_INTERVAL_SECONDS:
                    removed_captures = prune_old_files(CAPTURES_DIR, "capture_*.jpg", EVENT_RETENTION_DAYS)
                    removed_crops = prune_old_files(MESANGE_DIR, "*.jpg", EVENT_RETENTION_DAYS)
                    removed_clips = prune_old_files(EVENTS_VIDEO_DIR, "*.gif", EVENT_RETENTION_DAYS)
                    last_maintenance_at = now
                    if removed_captures or removed_crops or removed_clips:
                        logger.info(
                            "Maintenance cleanup: captures=%d crops=%d clips=%d",
                            removed_captures,
                            removed_crops,
                            removed_clips,
                        )

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
