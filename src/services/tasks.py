"""
Celery tasks for async video processing
"""

from celery import shared_task
from celery.signals import worker_process_init
from src.celeryconfig import app
from src.model_inference.yolo_inference import YOLOInference
from src.video_processor.video_processor import VideoProcessor
from src.config import YOLO_MODEL_PATH, CONFIDENCE_THRESHOLD, IOU_THRESHOLD, DEVICE
import logging

logger = logging.getLogger(__name__)

# Global model cache - one instance per worker process
_model_cache = None


@worker_process_init.connect
def init_worker_process(**kwargs):
    """
    Initialize YOLO model once per worker process.
    
    This signal handler is called when a Celery worker process starts.
    Loading the model here ensures it's loaded once and reused across
    all tasks in this worker process, improving performance significantly.
    """
    global _model_cache
    
    logger.info("🚀 Initializing YOLO model for worker process...")
    
    try:
        _model_cache = YOLOInference(
            model_path=str(YOLO_MODEL_PATH),
            confidence_threshold=CONFIDENCE_THRESHOLD,
            iou_threshold=IOU_THRESHOLD,
            device=DEVICE
        )
        logger.info("✅ YOLO model loaded successfully in worker process")
    except Exception as e:
        logger.error(f"❌ Failed to load YOLO model in worker process: {str(e)}")
        raise


def get_model() -> YOLOInference:
    """
    Get the cached YOLO model instance.
    
    Returns:
        YOLOInference: The cached model instance
        
    Raises:
        RuntimeError: If model cache is not initialized
    """
    if _model_cache is None:
        raise RuntimeError(
            "Model cache not initialized. "
            "This should not happen if worker_process_init ran correctly."
        )
    return _model_cache

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
        # Update task status: starting
        self.update_state(state="PROCESSING", meta={"current": 0, "status": "Starting video processing..."})
        
        # Get cached YOLO model (loaded once per worker process)
        model = get_model()
        
        # Override thresholds if different from cached model
        if (confidence_threshold != model.confidence_threshold or 
            iou_threshold != model.iou_threshold):
            # Note: These will be passed to predict() calls, not changing the model instance
            logger.info(
                f"Using custom thresholds: conf={confidence_threshold}, iou={iou_threshold} "
                f"(model defaults: conf={model.confidence_threshold}, iou={model.iou_threshold})"
            )
        
        # Update task status: processing video
        self.update_state(state="PROCESSING", meta={"current": 10, "status": "Processing video..."})
        
        # Process video with VideoProcessor
        # Pass custom thresholds to override cached model defaults if needed
        processor = VideoProcessor(model=model, fps_sample=fps_sample)
        results = processor.process_video(
            video_path,
            conf=confidence_threshold,
            iou=iou_threshold
        )
        
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