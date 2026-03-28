"""
Configuration centralisée du projet.
À adapter selon ton environnement Pi5.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CAPTURES_DIR = DATA_DIR / "captures"
STAGING_DIR = DATA_DIR / "staging"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"

MESANGE_DIR = DATA_DIR / "mesange"
EVENTS_VIDEO_DIR = DATA_DIR / "events_video"

# Créer dossiers s'ils n'existent pas
DATA_DIR.mkdir(exist_ok=True)
CAPTURES_DIR.mkdir(exist_ok=True)
STAGING_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
MESANGE_DIR.mkdir(exist_ok=True)
EVENTS_VIDEO_DIR.mkdir(exist_ok=True)

# ===== CAMERA =====
CAMERA_RESOLUTION = os.getenv("CAMERA_RESOLUTION", "3280x2464")
CAMERA_FRAMERATE = int(os.getenv("CAMERA_FRAMERATE", "20"))
CAPTURE_INTERVAL_SECONDS = float(os.getenv("CAPTURE_INTERVAL_SECONDS", "60"))

# ===== MOTION =====
MOTION_SCORE_THRESHOLD = float(os.getenv("MOTION_SCORE_THRESHOLD", "0.02"))
MOTION_RESIZE_WIDTH = int(os.getenv("MOTION_RESIZE_WIDTH", "320"))
MOTION_RESIZE_HEIGHT = int(os.getenv("MOTION_RESIZE_HEIGHT", "180"))

# ===== EVENT FILTERING =====
# Durée minimale (secondes) entre deux événements enregistrés. 0 = désactivé.
EVENT_COOLDOWN_SECONDS = float(os.getenv("EVENT_COOLDOWN_SECONDS", "0"))
# Si True, ne sauvegarder en DB que les events où YOLO détecte au moins un oiseau.
SAVE_BIRD_EVENTS_ONLY = os.getenv("SAVE_BIRD_EVENTS_ONLY", "false").lower() == "true"

# ===== EVENT CLIPS =====
EVENT_CLIP_ENABLED = os.getenv("EVENT_CLIP_ENABLED", "true").lower() == "true"
EVENT_CLIP_POST_FRAMES = int(os.getenv("EVENT_CLIP_POST_FRAMES", "6"))
EVENT_CLIP_FRAME_INTERVAL_SECONDS = float(os.getenv("EVENT_CLIP_FRAME_INTERVAL_SECONDS", "0.2"))
EVENT_CLIP_MAX_WIDTH = int(os.getenv("EVENT_CLIP_MAX_WIDTH", "960"))

# ===== DETECTION =====
YOLO_CONFIDENCE = float(os.getenv("YOLO_CONFIDENCE", "0.5"))
YOLO_IOU = float(os.getenv("YOLO_IOU", "0.45"))
YOLO_MODEL = MODELS_DIR / os.getenv("YOLO_MODEL", "yolo11n.onnx")

# ===== RECOGNITION =====
EMBEDDING_THRESHOLD = float(os.getenv("EMBEDDING_THRESHOLD", "0.7"))
MAX_INDIVIDUALS = int(os.getenv("MAX_INDIVIDUALS", "50"))
EMBEDDING_MODEL = MODELS_DIR / "mobilenetv2.tflite"

# ===== DATABASE =====
DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "birdfeeder.db"))

# ===== FLASK =====
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"

# ===== LOGGING =====
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / os.getenv("LOG_FILE", "birdfeeder.log")

# Debug
if __name__ == "__main__":
    print(f"Base dir: {BASE_DIR}")
    print(f"Data dir: {DATA_DIR}")
    print(f"DB: {DB_PATH}")
    print(f"YOLO model: {YOLO_MODEL}")
    print(f"Embedding model: {EMBEDDING_MODEL}")
