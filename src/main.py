"""
Entry point - Placeholder pour Phase 1.
"""
import logging
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer config
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LOG_FILE, LOG_LEVEL

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
    print("✅ Config loaded successfully")
    print("⏳ Phase 1 implementation coming next...")

if __name__ == "__main__":
    main()
