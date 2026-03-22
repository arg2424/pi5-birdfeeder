"""
Module capture caméra - Phase 1.
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CAPTURES_DIR, CAMERA_RESOLUTION

logger = logging.getLogger(__name__)

class CameraHandler:
    """Gestionnaire de caméra Pi5."""
    
    def __init__(self):
        self.resolution = CAMERA_RESOLUTION
        logger.info(f"📷 Camera initialized: {self.resolution}")
    
    def capture(self):
        """Capturer une image (Phase 1: placeholder)"""
        logger.info("📸 Capturing image...")
        # TODO: implement with libcamera/picamera2
        return None

if __name__ == "__main__":
    camera = CameraHandler()
