"""
Video processor for extracting frames and processing with YOLO model
Handles video file loading, frame extraction, and batch detection
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Callable
import logging
from tqdm import tqdm

from src.config import VIDEO_EXTENSIONS, DEFAULT_FPS_SAMPLE
from src.model_inference import YOLOInference

logger = logging.getLogger(__name__)

class VideoProcessor:
    """
    Process video files and extract detections from each frame
    
    Handles:
    - Video file validation and loading
    - Frame extraction at specified intervals
    - Batch processing with YOLOInference
    - Detection aggregation and statistics
    """
    
    def __init__(
        self,
        model: YOLOInference,
        fps_sample: int = DEFAULT_FPS_SAMPLE,
    ):
        """
        Initialize VideoProcessor
        
        Args:
            model: YOLOInference instance for predictions
            fps_sample: Extract 1 frame every N frames (1 = every frame, 2 = every 2nd frame)
        """
        self.model = model
        self.fps_sample = fps_sample
        self.video_path = None
        self.cap = None
        self.total_frames = 0
        self.fps = 0
        self.frame_width = 0
        self.frame_height = 0
        self.detections_by_frame = {}
        
        logger.info(f"VideoProcessor initialized with fps_sample={fps_sample}")

    def load_video(self, video_path: str) -> bool:
        """
        Load and validate video file
        
        Args:
            video_path: Path to video file
            
        Returns:
            True if loaded successfully, False otherwise
        """
        video_path = Path(video_path)
        
        # Validate file exists
        if not video_path.exists():
            logger.error(f"Video file not found: {video_path}")
            return False
        
        # Validate extension
        if video_path.suffix.lower() not in VIDEO_EXTENSIONS:
            logger.error(
                f"Unsupported video format: {video_path.suffix}. "
                f"Supported: {VIDEO_EXTENSIONS}"
            )
            return False
        
        # Open video
        self.cap = cv2.VideoCapture(str(video_path))
        if not self.cap.isOpened():
            logger.error(f"Failed to open video: {video_path}")
            return False
        
        # Get video properties
        self.video_path = video_path
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        logger.info(
            f"Video loaded: {video_path.name} "
            f"({self.total_frames} frames @ {self.fps:.1f} fps, "
            f"{self.frame_width}x{self.frame_height})"
        )
        return True
    
    def extract_frames(
        self,
        fps_sample: Optional[int] = None,
        callback: Optional[Callable] = None,
    ) -> List[np.ndarray]:
        """
        Extract frames from loaded video
        
        Args:
            fps_sample: Override default fps_sample (1 = every frame)
            callback: Optional callback function called for each frame
                     callback(frame, frame_number)
            
        Returns:
            List of extracted frames (numpy arrays)
        """
        if self.cap is None:
            logger.error("No video loaded. Call load_video() first")
            return []
        
        # Use provided fps_sample only if explicitly passed (not None)
        # Treat None as the only "use default" value
        if fps_sample is None:
            fps_sample = self.fps_sample
        
        # Validate that fps_sample is a positive integer to prevent ZeroDivisionError
        if not isinstance(fps_sample, int) or isinstance(fps_sample, bool) or fps_sample <= 0:
            logger.error(f"fps_sample must be a positive integer, got: {fps_sample}")
            return []
        
        frames = []
        frame_count = 0
        extracted_count = 0
        
        logger.info(f"Extracting frames (sample rate: 1/{fps_sample})")
        
        with tqdm(total=self.total_frames, desc="Extracting frames") as pbar:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                # Sample frames based on fps_sample
                if frame_count % fps_sample == 0:
                    frames.append(frame)
                    extracted_count += 1
                    
                    if callback:
                        callback(frame, frame_count)
                    
                frame_count += 1
                pbar.update(1)
        
        # Reset video position
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        logger.info(f"Extracted {extracted_count} frames from {self.total_frames} total")
        return frames
    
    def process_frames(
        self,
        frames: List[np.ndarray],
        conf: Optional[float] = None,
        iou: Optional[float] = None,
    ) -> Dict[int, List[Dict]]:
        """
        Run YOLO inference on list of frames
        
        Args:
            frames: List of frames (numpy arrays)
            conf: Confidence threshold override
            iou: IoU threshold override
            
        Returns:
            Dict mapping frame_index -> list of detections
            {
                0: [{"class_name": "Nike", "confidence": 0.92, ...}],
                1: [{"class_name": "Adidas", "confidence": 0.87, ...}],
                ...
            }
        """
        detections = {}
        
        logger.info(f"Processing {len(frames)} frames with YOLO model")

        for frame_idx, frame in enumerate(tqdm(frames, desc="Running inference")):
            result = self.model.predict(frame, conf=conf, iou=iou)
            detections[frame_idx] = result["detections"]
        
        self.detections_by_frame = detections
        logger.info(f"Processed {len(frames)} frames")
        return detections
    
    def process_video(
        self,
        video_path: str,
        conf: Optional[float] = None,
        iou: Optional[float] = None,
    ) -> Dict:
        """
        Complete pipeline: load video -> extract frames -> process frames
        
        Args:
            video_path: Path to video file
            conf: Confidence threshold override
            iou: IoU threshold override
            
        Returns:
            Dictionary with complete processing results:
            {
                "video_path": str,
                "total_frames": int,
                "processed_frames": int,
                "fps": float,
                "duration_seconds": float,
                "detections_by_frame": {...},
                "statistics": {...}
            }
        """
        try:
            # Load video
            if not self.load_video(video_path):
                return {"error": f"Failed to load video: {video_path}"}
            
            # Extract frames
            frames = self.extract_frames()
            if not frames:
                return {"error": "No frames extracted from video"}
            
            # Process frames
            detections = self.process_frames(frames, conf=conf, iou=iou)
            
            # Calculate statistics
            stats = self._calculate_statistics(detections)
            
            result = {
                "video_path": str(self.video_path),
                "total_frames": self.total_frames,
                "processed_frames": len(frames),
                "fps": self.fps,
                "duration_seconds": self.total_frames / self.fps if self.fps > 0 else 0,
                "frame_dimensions": (self.frame_height, self.frame_width),
                "detections_by_frame": detections,
                "statistics": stats,
            }
            
            logger.info("Video processing completed")
            return result
        finally:
            # Always close the video capture to prevent resource leaks
            self.close()
    
    def _calculate_statistics(
        self,
        detections: Dict[int, List[Dict]]
    ) -> Dict:
        """
        Calculate aggregated statistics from detections
        
        Args:
            detections: Dict of frame_idx -> list of detections
            
        Returns:
            Statistics dictionary:
            {
                "total_detections": int,
                "unique_classes": int,
                "by_class": {
                    "Nike": {
                        "count": 150,
                        "avg_confidence": 0.92,
                        "frames_with_detection": [0, 1, 2, ...],
                        "first_frame": 0,
                        "last_frame": 3599
                    }
                }
            }
        """
        stats = {
            "total_detections": 0,
            "unique_classes": set(),
            "by_class": {}
        }
        
        # Aggregate by class
        for frame_idx, frame_detections in detections.items():
            for det in frame_detections:
                class_name = det["class_name"]
                
                # Initialize class if not seen
                if class_name not in stats["by_class"]:
                    stats["by_class"][class_name] = {
                        "count": 0,
                        "confidences": [],
                        "frames_with_detection": [],
                        "first_frame": frame_idx,
                        "last_frame": frame_idx,
                    }

                confidence = det["confidence"]

                # Update class stats
                stats["by_class"][class_name]["count"] += 1
                stats["by_class"][class_name]["confidences"].append(confidence)
                stats["by_class"][class_name]["frames_with_detection"].append(frame_idx)
                stats["by_class"][class_name]["last_frame"] = frame_idx
                
                stats["total_detections"] += 1
                stats["unique_classes"].add(class_name)
        
        # Calculate averages and clean up
        for class_name, class_stats in stats["by_class"].items():
            confidences = class_stats.pop("confidences")
            class_stats["avg_confidence"] = (
                sum(confidences) / len(confidences) if confidences else 0
            )
            class_stats["frames_with_detection"] = list(
                set(class_stats[f"frames_with_detection"])   
            )
            class_stats["screen_time_frames"] = len(
                class_stats["frames_with_detection"]
            )
        
        stats["unique_classes"] = len(stats["unique_classes"])
        
        return stats
    
    def get_detections(self) -> Dict[int, List[Dict]]:
        """Get all detections from last processing"""
        return self.detections_by_frame
    
    def close(self) -> None:
        """Close video file and cleanup"""
        if self.cap is not None:
            self.cap.release()
            logger.info("Video file closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    def __repr__(self) -> str:
        return (
            f"VideoProcessor(video={self.video_path.name if self.video_path else 'None'}, "
            f"fps_sample={self.fps_sample}, "
            f"total_frames={self.total_frames})"
        )