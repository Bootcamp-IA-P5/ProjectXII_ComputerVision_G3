"""
Centralized configuration for the entire project
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project directories
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
DATASET_DIR = PROJECT_ROOT / "dataset_yolov8"

# Model configuration
YOLO_MODEL_PATH = MODELS_DIR / "trained" / "best_yolov8x_Kiru.pt"
YOLO_MODEL_PATH_ONNX = MODELS_DIR / "trained" / "best_yolov8x_Kiru.onnx"

# Video processing
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv"}
DEFAULT_FPS_SAMPLE = 1  # Extract 1 frame per second

# Model inference
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
IOU_THRESHOLD = float(os.getenv("IOU_THRESHOLD", "0.45"))
DEVICE = os.getenv("DEVICE", "auto")  # auto, cpu, cuda

# Database (Phase 2)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./project_cv.db")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Ensure directories exist
def ensure_directories_initialized() -> None:
    """
    Create required project directories if they do not already exist.

    This function is intentionally side-effectful and should be called
    explicitly by application entry points, rather than at import time.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "detections").mkdir(parents=True, exist_ok=True)