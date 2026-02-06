"""Reprocess video with updated confidence threshold"""
import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv(override=True)

import os
print(f"Confidence threshold: {os.environ.get('CONFIDENCE_THRESHOLD')}")
print("Processing Video1_DHL.mp4...")

from src.database.database import reset_connection, init_db
reset_connection()
init_db()

from src.model_inference import YOLOInference
from src.video_processor import VideoProcessor

model = YOLOInference()
print(f"Model loaded on: {model.device}")

processor = VideoProcessor(model, fps_sample=1)
result = processor.process_video("videos/Video1_DHL.mp4", save_to_db=True, model_name="YOLOv8x_Kiru_conf025")

if "error" in result:
    print(f"ERROR: {result['error']}")
else:
    stats = result.get("statistics", {})
    print(f"Done! ID={result.get('db_video_id')}")
    print(f"Brands: {stats.get('unique_classes', 0)}, Detections: {stats.get('total_detections', 0)}")
