"""
Analysis service for video processing and detection aggregation
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from src.model_inference.yolo_inference import YOLOInference
from src.video_processor.video_processor import VideoProcessor
from src.config import VIDEO_UPLOAD_DIR
import logging

logger = logging.getLogger(__name__)

class AnalysisService:
    """
    Orchestrates video analysis workflow without ORM dependencies.
    
    Responsibilities:
    - Coordinate VideoProcessor + YOLOInference
    - Extract video metadata
    - Aggregate detection results
    - Prepare data for database persistence (by tasks.py)
    """
    
    def __init__(self, model: YOLOInference):
        """
        Initialize analysis service with a YOLO model instance.
        
        Args:
            model: YOLOInference instance (already loaded)
        """
        self.model = model
        self.processor = VideoProcessor(model=model)
    
    def analyze_video(self, video_id: int, video_path: str, fps_sample: int = 1) -> Dict[str, Any]:
        """
        Main analysis method: process video and return structured results.
        
        Args:
            video_id: Database ID of video (for tracking)
            video_path: Full path to video file
            fps_sample: Extract 1 frame every fps_sample frames
            
        Returns:
            dict with keys:
                - video_id: int
                - success: bool
                - metadata: dict (fps, duration, frame_count, dimensions)
                - detections_by_frame: dict (frame_idx -> list of detections)
                - statistics: dict (total_detections, unique_brands, by_class)
                - error: str (if success=False)
        """
        try: 
            # Validate video exists
            video_path_obj = Path(video_path)
            if not video_path_obj.exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            results = self.processor.process_video(video_path, fps_sample)
            
            
            metadata = {
                "fps": results["fps"], 
                "duration_seconds": results["duration_seconds"], 
                "total_frames": results["processed_frames"], 
                "frame_width": results["frame_dimensions"][1], 
                "frame_height": results["frame_dimensions"][0],
            }
                        
            return {
                "video_id": video_id,
                "success": True,
                "metadata": metadata,
                "detections_by_frame": results["detections_by_frame"],
                "statistics": results["statistics"]
            } 
        
        except Exception as e:
            logger.error(f"Analysis failed for video {video_id}: {str(e)}")
            return {
                "video_id": video_id,
                "success": False,
                "error": str(e),
                "metadata": {},
                "detections_by_frame": {},
                "statistics": {}
            }            
            
    def extract_crop_images(self, video_path: str, video_id: int,
                            detections_by_frame: Dict[int, List[Dict]]) -> Dict[str, List[str]]:
        """
        Extract crop images from video frames based on detection bboxes.
        
        Args:
            video_path: Path to video file
            video_id: Video ID for directory structure
            detections_by_frame: Results from analyze_video()
            
        Returns:
            dict: {frame_idx -> list of crop file paths}
            
        NOTE: Implementation for storage strategy (local/Supabase) comes later
        """
        # TODO: Implementation placeholder
        logger.info(f"Crop extraction for video {video_id} - to be implemented")
        return {}