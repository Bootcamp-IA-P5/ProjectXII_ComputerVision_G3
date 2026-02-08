"""
Pydantic schemas for request/response validation
Define the structure of data coming in and going out
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Union
from datetime import datetime


# ============================================================================
# REQUEST SCHEMAS (What the server receives)
# ============================================================================

class VideoUploadRequest(BaseModel):
    """
    Schema for POST /upload endpoint

    Fields:
        confidence_threshold: Min confidence for detections (0-1)
        iou_threshold: IoU threshold for NMS (0-1)
        fps_sample: Extract 1 frame every N frames
    """
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    iou_threshold: float = Field(default=0.45, ge=0.0, le=1.0)
    fps_sample: int = Field(default=1, ge=1)


# ============================================================================
# RESPONSE SCHEMAS (What the server returns)
# ============================================================================

class VideoResponse(BaseModel):
    """
    Schema for GET /videos endpoint (list of videos)

    Returns basic video metadata without detections
    """
    id: Union[int, str]
    filename: str
    duration_seconds: float
    total_frames: int
    fps: float
    frame_width: int
    frame_height: int
    is_processed: bool
    total_detections: Optional[int] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Allow ORM models to be converted


class DetectionResponse(BaseModel):
    """
    Schema for each individual detection

    Represents a single logo detection in a frame
    """
    id: int
    brand_id: int
    brand_name: str
    confidence: float
    bbox_x1: int
    bbox_y1: int
    bbox_x2: int
    bbox_y2: int
    bbox_width: int
    bbox_height: int
    frame_number: int

    class Config:
        from_attributes = True


class BrandSummaryResponse(BaseModel):
    """
    Summary statistics for a single brand across entire video
    """
    brand_name: str
    detections: int
    avg_confidence: float
    screen_time_frames: int
    screen_time_seconds: float
    first_frame: int
    last_frame: int


class VideoResultsResponse(BaseModel):
    """
    Complete response for GET /videos/{id}/results

    This is the "mega response" with everything:
    - Video metadata
    - All detections
    - Statistics per brand
    - Processing info
    """
    video: VideoResponse
    total_detections: int
    unique_brands: int
    brands: Dict[str, BrandSummaryResponse]
    detections_by_frame: Dict[int, List[DetectionResponse]]
    processing_time_seconds: Optional[float] = None
    confidence_threshold: float
    iou_threshold: float
    fps_sample: int

    class Config:
        from_attributes = True


class UploadResponseSchema(BaseModel):
    """
    Response for POST /upload

    Returned immediately after file upload starts processing
    """
    video_id: Union[int, str]
    filename: str
    status: str  # "queued", "processing", "completed", "failed"
    task_id: str
    message: str

    class Config:
        from_attributes = True