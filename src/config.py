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
YOLO_MODEL_NAME = os.getenv("YOLO_MODEL_NAME", "best_yolo11x_finetunedPG_Kiru.pt")
YOLO_MODEL_PATH = MODELS_DIR / "trained" / YOLO_MODEL_NAME
YOLO_MODEL_PATH_ONNX = MODELS_DIR / "trained" / YOLO_MODEL_NAME.replace(".pt", ".onnx")

# Video processing
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv"}
DEFAULT_FPS_SAMPLE = 1  # Extract 1 frame per second

# Model inference
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.15"))
IOU_THRESHOLD = float(os.getenv("IOU_THRESHOLD", "0.45"))
DEVICE = os.getenv("DEVICE", "auto")  # auto, cpu, cuda

# Database (Phase 2)
DATABASE_URL = os.getenv("DATABASE_URL")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_RELOAD = os.getenv("API_RELOAD", "false").lower() in ("true", "1", "yes")

# CORS - Allowed Origins
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
]

# VIDEO Upload Directory
VIDEO_UPLOAD_DIR = DATA_DIR / "uploads" / "videos"

# Ensure directories exist
def ensure_directories_initialized() -> None:
    """
    Create required project directories if they do not already exist.

    This function is intentionally side-effectful and should be called
    explicitly by application entry points, rather than at import time.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "detections").mkdir(parents=True, exist_ok=True)
    VIDEO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)