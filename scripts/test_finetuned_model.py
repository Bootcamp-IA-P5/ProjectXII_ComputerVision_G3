"""
Test script for fine-tuned YOLO model on video files
"""

import cv2
import sys
from pathlib import Path
from collections import defaultdict

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import YOLO_MODEL_PATH, CONFIDENCE_THRESHOLD, VIDEO_UPLOAD_DIR
from src.model_inference.yolo_inference import YOLOInference


def test_video(video_path: str, model_inference: YOLOInference):
    """Process video and show detections"""
    
    print(f"\n{'='*60}")
    print(f"Testing: {Path(video_path).name}")
    print(f"{'='*60}")
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Error: Cannot open video {video_path}")
        return
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_interval = int(fps)  # Sample every 1 second
    
    frame_count = 0
    detections_per_frame = defaultdict(list)
    total_detections = 0
    
    print(f"FPS: {fps}, Total frames: {total_frames}")
    print(f"Sampling every {frame_interval} frames (1 per second)\n")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Sample every N frames
        if frame_count % frame_interval == 0:
            results = model_inference.predict(frame, conf_threshold=CONFIDENCE_THRESHOLD)
            
            detections = results.get("detections", [])
            if detections:
                print(f"Frame {frame_count:4d} ({frame_count/fps:.1f}s): {len(detections)} detection(s)")
                for det in detections:
                    class_name = det.get("class_name", "Unknown")
                    confidence = det.get("confidence", 0)
                    print(f"  → {class_name}: {confidence:.2f}")
                    total_detections += 1
            else:
                print(f"Frame {frame_count:4d} ({frame_count/fps:.1f}s): No detections")
        
        frame_count += 1
    
    cap.release()
    print(f"\nTotal detections: {total_detections}")


def main():
    print(f"Model path: {YOLO_MODEL_PATH}")
    print(f"Confidence threshold: {CONFIDENCE_THRESHOLD}")
    
    # Check model exists
    if not YOLO_MODEL_PATH.exists():
        print(f"❌ Model not found: {YOLO_MODEL_PATH}")
        return
    
    print(f"✓ Model found")
    
    # Load model
    print("\nLoading model...")
    try:
        model_inference = YOLOInference()
        print("✓ Model loaded successfully")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return
    
    # Test videos
    videos = [
        VIDEO_UPLOAD_DIR / "VideoYT_Paypal.mp4",
        VIDEO_UPLOAD_DIR / "Google_Kiru2.mp4"
    ]
    
    for video in videos:
        if video.exists():
            test_video(str(video), model_inference)
        else:
            print(f"⚠️ Video not found: {video}")


if __name__ == "__main__":
    main()