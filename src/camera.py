"""
Module capture caméra - Phase 1.
"""
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path

parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from config import CAMERA_RESOLUTION, CAPTURES_DIR, STAGING_DIR

logger = logging.getLogger(__name__)


def _parse_resolution(value):
    """Convertit une resolution string en tuple (w, h)."""
    if isinstance(value, tuple) and len(value) == 2:
        return value
    if isinstance(value, str):
        normalized = value.lower().replace(" ", "").replace(",", "x")
        if "x" in normalized:
            w_str, h_str = normalized.split("x", 1)
            return (int(w_str), int(h_str))
    raise ValueError(f"Invalid CAMERA_RESOLUTION: {value}")

class CameraHandler:
    """Gestionnaire de caméra Pi5."""
    
    def __init__(self):
        self.resolution = _parse_resolution(CAMERA_RESOLUTION)
        self.camera = None
        logger.info(f"📷 Camera initialized: {self.resolution}")

    def cleanup_staging(self):
        """Supprimer les images temporaires restantes d'un précédent run."""
        removed_files = 0
        for image_path in STAGING_DIR.glob("staging_*.jpg"):
            image_path.unlink(missing_ok=True)
            removed_files += 1
        logger.info("🧹 Staging cleaned: %s file(s) removed", removed_files)
    
    def _init_camera(self):
        """Initialiser la caméra si pas déjà fait."""
        if self.camera is None:
            try:
                from picamera2 import Picamera2
                self.camera = Picamera2()
                config = self.camera.create_still_configuration(
                    main={"size": self.resolution}
                )
                self.camera.configure(config)
                self.camera.start()
                logger.info("📷 Camera started successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize camera: {e}")
                raise
    
    def capture_image(self) -> str:
        """
        Capturer une image et la sauvegarder.
        
        Returns:
            str: Chemin du fichier image capturé
        """
        try:
            self._init_camera()
            
            # Générer nom de fichier avec timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}.jpg"
            filepath = CAPTURES_DIR / filename
            
            # Capturer et sauvegarder
            logger.info(f"📸 Capturing image to {filepath}")
            self.camera.capture_file(str(filepath))
            
            logger.info(f"✅ Image captured: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Capture failed: {e}")
            raise

    def capture_staging_image(self) -> str:
        """Capturer une image temporaire pour l'analyse de mouvement."""
        try:
            self._init_camera()

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"staging_{timestamp}.jpg"
            filepath = STAGING_DIR / filename

            logger.info(f"📸 Capturing staging image to {filepath}")
            self.camera.capture_file(str(filepath))

            logger.info(f"✅ Staging image captured: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"❌ Staging capture failed: {e}")
            raise

    def persist_image(self, source_path: str) -> str:
        """Copier une image de staging vers l'archive durable."""
        source = Path(source_path)
        target = CAPTURES_DIR / source.name.replace("staging_", "capture_")
        shutil.copy2(source, target)
        logger.info("✅ Motion capture persisted: %s", target)
        return str(target)
    
    def close(self):
        """Fermer proprement la caméra."""
        if self.camera:
            self.camera.stop()
            self.camera.close()
            self.camera = None
            logger.info("📷 Camera closed")

if __name__ == "__main__":
    camera = CameraHandler()
    try:
        image_path = camera.capture_image()
        print(f"✅ Image captured: {image_path}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        camera.close()
