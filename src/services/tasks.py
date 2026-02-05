"""
Celery tasks for async video processing
"""

from celery import shared_task
from src.model_inference.yolo_inference import YOLOInference
from src.video_processor.video_processor import VideoProcessor
from src.config import YOLO_MODEL_PATH, CONFIDENCE_THRESHOLD, IOU_THRESHOLD, DEVICE
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def process_video_task(self, video_id: int, video_path: str,
                       confidence_threshold: float = CONFIDENCE_THRESHOLD,
                       iou_threshold: float = IOU_THRESHOLD,
                       fps_sample: int = 1):
    """
    Celery task to process a video asynchronously.
    
    Args:
        self: Celery task instance (bind=True allows self reference)
        video_id: Database ID of the video
        video_path: Full path to the video file
        confidence_threshold: Detection confidence threshold (0.0-1.0)
        iou_threshold: NMS IOU threshold (0.0-1.0)
        fps_sample: Extract 1 frame every fps_sample frames
        
    Returns:
        dict: Processing results with metadata, detections, and statistics
    """
    try:
        # Update task status: processing
        self.update_state(state="PROCESSING", meta={"current": 0, "status": "Loading model..."})
        
        # Initialize YOLO model
        model = YOLOInference(
            model_path=str(YOLO_MODEL_PATH),
            confidence_threshold=confidence_threshold,
            iou_threshold=iou_threshold,
            device=DEVICE
        )
        
        # Update task status: processing video
        self.update_state(state="PROCESSING", meta={"current": 25, "status": "Processing video..."})
        
        # Process video with VideoProcessor
        processor = VideoProcessor(model=model, fps_sample=fps_sample)
        results = processor.process_video(video_path)
        
        # Update task status: complete
        self.update_state(state="PROCESSING", meta={"current": 100, "status": "Complete"})
        
        logger.info(f"Video {video_id} processed successfully. Detections: {results['statistics']['total_detections']}")

        return {
            "video_id": video_id,
            "success": True,
            "results": results,
        }
    
    except Exception as e:
        logger.error(f"Error processing video {video_id}: {str(e)}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "video_id": video_id}
        )
        return {
            "video_id": video_id,
            "success": False,
            "error": str(e),
        }