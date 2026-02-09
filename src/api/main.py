""" 
FastAPI application for video analysis API

Handles:
- Video upload and processing
- Results retrieval
- Brand statistics

What happens when you upload a video?
1. React sends: POST /upload with file + parameters
2. FastAPI receives in upload_video()
3. Validates: does the file exist?
4. Saves: Writes file to disk
5. Registers: Creates row in "videos" table
6. Returns: {"video_id": 1, "status": "pending", ...}
7. React receives JSON and displays "Video uploaded"

What happens when you request results?
1. React sends: GET /videos/1/results
2. FastAPI retrieves video from DB
3. Gets ALL detections for video 1
4. Groups by brand: {"Nike": [det1, det2], "Adidas": [det3]}
5. Calculates: averages, screen time, first/last frame
6. Returns: Giant JSON with EVERYTHING
7. React displays charts with the data"""

import logging
from pathlib import Path # Handles file paths
from datetime import datetime # Timestamps
from typing import Dict, List # Type hints
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware # CORS for React
from sqlalchemy.orm import Session 
import cv2

from src.config import API_HOST, API_PORT, API_RELOAD, ALLOWED_ORIGINS, VIDEO_UPLOAD_DIR, DEVICE, CONFIDENCE_THRESHOLD, IOU_THRESHOLD
from src.database.init_db import init_db, get_db
# Database models for ORM queries
from src.database.models import Video, Detection, Brand, VideoBrandStats
from src.api.schemas import (
    VideoUploadRequest,
    VideoResponse,
    VideoResultsResponse,
    UploadResponseSchema,
)

logger = logging.getLogger(__name__)

# CREATE APP (FastAPI instance)
app = FastAPI(
    title="ProjectXII Computer Vision API",
    description="Video analysis with logo detection",
    version="1.0.0",
)

# CORS (So React can communicate with FastAPI)
# CORS = Cross-Origin Resource Sharing
# Without this React cannot call FastAPI, it's like a firewall that allows/rejects requests from other domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Which domains can access
    allow_credentials=True,         # Allows cookies/auth
    allow_methods=["*"],            # GET, POST, DELETE...
    allow_headers=["*"]             # Any header
)


# EVENTS (Startup/Shutdown)
@app.on_event("startup")
async def startup_event():
    """
    Executes when STARTING the application
    
    Here we initialize things we need before processing requests

    """
    try:
        logger.info("🚀 Starting API...")
        
        # Create DB tables if they don't exist
        init_db()
        logger.info("✅ Database initialized")

        # Create uploads folder if it doesn't exist
        VIDEO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("✅ Upload directories created")

        logger.info("🚀 API started successfully")
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise



@app.on_event("shutdown")
async def shutdown_event():
    """
    Executes when SHUTTING DOWN the application
    We clean up resources (close connections, etc)

    """
    logger.info("🛑 Shutting down API...")
    logger.info("✅ Cleanup completed")

# ENDPOINTS
@app.get("/")
async def root():
    """
    Basic endpoint - returns API info
        
    Use to verify if the API is accessible
    
    Returns:
        {"status": "ok", "message": "API running"}
    """
    # Returns a dictionary that is automatically converted to JSON
    return {
        "status": "ok",
        "message": "API running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check endpoint
    
    Checks:
    - API responsiveness
    - Database connectivity
    - Model file availability
    
    Returns:
        Health status with component details
    """
    from pathlib import Path
    from src.config import YOLO_MODEL_PATH
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "components": {}
    }
    
    # Check database connectivity
    try:
        # Execute a simple query to verify DB connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        health_status["components"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
        logger.error(f"Health check - DB error: {e}")
    
    # Check model file availability
    try:
        model_path = Path(YOLO_MODEL_PATH)
        if model_path.exists():
            model_size_mb = model_path.stat().st_size / (1024 * 1024)
            health_status["components"]["model"] = {
                "status": "healthy",
                "message": f"Model file available ({model_size_mb:.1f} MB)",
                "path": str(model_path.name)
            }
        else:
            health_status["status"] = "degraded"
            health_status["components"]["model"] = {
                "status": "unhealthy",
                "message": f"Model file not found at {model_path}"
            }
    except Exception as e:
        health_status["components"]["model"] = {
            "status": "unknown",
            "message": f"Could not check model: {str(e)}"
        }
    
    # Check upload directory
    try:
        if VIDEO_UPLOAD_DIR.exists():
            health_status["components"]["storage"] = {
                "status": "healthy",
                "message": "Upload directory accessible"
            }
        else:
            health_status["components"]["storage"] = {
                "status": "degraded",
                "message": "Upload directory does not exist"
            }
    except Exception as e:
        health_status["components"]["storage"] = {
            "status": "unknown",
            "message": f"Could not check storage: {str(e)}"
        }
    
    # Return appropriate HTTP status code
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status

@app.post("/upload", response_model=UploadResponseSchema)
async def upload_video(
    file: UploadFile = File(...),
    confidence_threshold: float = Form(default=CONFIDENCE_THRESHOLD, ge=0.0, le=1.0),
    iou_threshold: float = Form(default=IOU_THRESHOLD, ge=0.0, le=1.0),
    fps_sample: int = Form(default=1, ge=1),
    db: Session = Depends(get_db)
):    
    """
    Upload and process video
    
    What it does:
    1. Validates that the file exists
    2. Saves file to disk
    3. Creates record in DB
    4. Returns video ID

    Args:
        file: Video file MP4/AVI/MOV
        confidence_threshold: Min confidence for detections (0-1), default 0.5
        iou_threshold: IoU threshold for NMS (0-1), default 0.45
        fps_sample: Extract 1 frame every N frames, default 1
        db: DB connection (injected by FastAPI)
        
    Returns:
        UploadResponseSchema with:
        - video_id: ID assigned in DB
        - filename: File name
        - status: "pending" (will be processed)
        - message: Informative message
    """
    from src.services.tasks import process_video_task
    from uuid import uuid4
    
    try: 
        # Step 1: Validate that the file exists and has a name
        if not file or not file.filename:
            logger.warning("⚠️ Upload attempt without file")
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Step 2: Save file to disk 
        # Read file contents
        contents = await file.read()
        
        # Create path with unique name to avoid overwrites
        original_name = Path(file.filename)
        unique_filename = f"{uuid4().hex}{original_name.suffix}"
        file_path = VIDEO_UPLOAD_DIR / unique_filename
        
        # Write contents to disk 
        file_path.write_bytes(contents)
        logger.info(f"✅ File saved: {file_path}")
        
        # Step 3: Extract basic metadata and create DB record
        # Use cv2 to get metadata immediately so we can create a valid Video record
        cap = cv2.VideoCapture(str(file_path))
        if not cap.isOpened():
             raise HTTPException(status_code=400, detail="Could not open uploaded video file")
             
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps if fps > 0 else 0
        cap.release()

        video = Video(
            filename=file.filename,
            filepath=str(file_path),
            total_frames=total_frames,
            processed_frames=0,
            fps=fps,
            duration_seconds=duration,
            frame_width=width,
            frame_height=height,
            confidence_threshold=confidence_threshold
        )
        db.add(video)
        db.commit()
        db.refresh(video)
        video_id = video.id
        
        # Step 4: Enqueue Celery task to process video
        task = process_video_task.delay(
            video_id=video_id,
            video_path=str(file_path),
            confidence_threshold=confidence_threshold,
            iou_threshold=iou_threshold,
            fps_sample=fps_sample
        )
        logger.info(f"✅ Video processing task queued: {task.id} (Video ID: {video_id})")

        # Step 5: Return response that FastAPI converts to JSON
        return UploadResponseSchema(
            video_id=video_id,
            filename=file.filename,
            status="queued",
            message=f"Video '{file.filename}' uploaded. Processing started. Task ID: {task.id}"
        )
    
    except HTTPException:
        # If it's an HTTP error, propagate
        raise
    
    except Exception as e:
        # Any other error
        logger.error(f"❌ Upload error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )

@app.get("/videos", response_model=list[VideoResponse])
async def list_videos(db: Session = Depends(get_db)):
    """
    List all uploaded videos
    
    What it does:
    1. Query DB: gets ALL videos
    2. Returns list of VideoResponse (JSON)
    
    Returns:
        List of VideoResponse:
        [
            {"id": 1, "filename": "video1.mp4", "duration_seconds": 120.5, ...},
            {"id": 2, "filename": "video2.mp4", "duration_seconds": 95.2, ...}
        ]
    """
    try:
        # Query "Get ALL videos from the table"
        videos = db.query(Video).all()
        logger.info(f"✅ Retrieved {len(videos)} videos from database")
        
        return videos
    
    except Exception as e:
        logger.error(f"❌ List videos error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list videos")
    
    
@app.get("/videos/{video_id}", response_model=VideoResponse)
async def get_video(video_id: int, db: Session = Depends(get_db)):
    """
    Get single video metadata

    What it does:
    1. Query DB: gets a specific video
    2. If it doesn't exist → 404 error
    3. Returns VideoResponse (JSON)
    
    Args:
        video_id: Video ID (e.g.: /videos/1)
        
    Returns:
        VideoResponse with video info
    """
    try:
        # Query: "Get the video whose id == video_id"
        # .filter() = WHERE in SQL
        # .first() = returns the 1st record or None
        video = db.query(Video).filter(Video.id == video_id).first()
        
        # If nothing is found, .first() returns None
        if not video:
            logger.warning(f"⚠️ Video {video_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"Video with ID {video_id} not found"
            )
        logger.info(f"✅ Retrieved video {video_id}")
        return video
    
    except HTTPException:
        raise # HTTP Error
    except Exception as e:
        logger.error(f"❌ Get video error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get video")
        
@app.get("/videos/{video_id}/results", response_model=VideoResultsResponse)
async def get_video_results(video_id: int, db: Session = Depends(get_db)):
    """
    Get complete results including detections and statistics

    THE MOST COMPLEX    
    What it does:
    1. Gets video
    2. Gets ALL detections for the video
    3. Groups by frame and by brand
    4. Calculates statistics
    5. Builds response with EVERYTHING
    
    Returns:
        VideoResultsResponse with:
        - video: Video metadata
        - total_detections: Total count
        - unique_brands: How many different brands
        - brands: Dict with stats per brand
        - detections_by_frame: Detections organized by frame
    """
    try:
        # Step 1: Get video
        video = db.query(Video).filter(Video.id == video_id).first()
        
        if not video:
            logger.warning(f"⚠️ Video {video_id} not found")
            raise HTTPException(status_code=404, detail="Video not found")
      
        # Step 2: Get ALL detections for this video
        # .join(Brand) = connects with Brand table to get name
        detections = (
            db.query(Detection)
            .join(Brand)
            .filter(Detection.video_id == video_id)
            .all()
        )
        
        logger.info(f"✅ Retrieved {len(detections)} detections for video {video_id}")
        
        # Step 3: Group detections by frame
        # Result: {0: [det1, det2], 1: [det3], ...}
        detections_by_frame: Dict[int, List] = {}
        for det in detections:
            frame_num = det.frame_number or 0   # If no frame_number, use 0
            if frame_num not in detections_by_frame:
                detections_by_frame[frame_num] = []
            detections_by_frame[frame_num].append(det)
        
        # Step 4: Calculate statistics per BRAND
        # Result: {"Nike": {"count": 50, "avg_confidence": 0.85, ...}, ...}
        brands_stats: Dict = {}
        
        for det in detections:
            brand_name = det.brand.name     # Get related brand name
            
            # If it's the first time we see this brand, create entry
            if brand_name not in brands_stats:
                brands_stats[brand_name] = {
                    "detections": 0, 
                    "confidences": [],   # To calculate average later
                    "frames": set(),    # To count unique frames
                }
        
            # Add data
            brands_stats[brand_name]["detections"] += 1
            brands_stats[brand_name]["confidences"].append(det.confidence)
            brands_stats[brand_name]["frames"].add(det.frame_number or 0)
        
        # Step 5: Process statistics (calculate averages, etc)
        brands_final = {}
        for brand_name, stats in brands_stats.items():
            # Calculate average confidence
            avg_conf = (
                sum(stats["confidences"]) / len(stats["confidences"])
                if stats["confidences"]
                else 0.0
            )
            
            # Convert frames set to list and sort
            frames_list = sorted(list(stats["frames"]))
            
            # Calculate screen time
            screen_time_frames = len(frames_list)
            screen_time_seconds = (
                screen_time_frames / video.fps if video.fps > 0 else 0
            )
        
            # Build response for this brand
            brands_final[brand_name] = {
                "brand_name": brand_name,
                "detections": stats["detections"],
                "avg_confidence": round(avg_conf, 3),
                "screen_time_frames": screen_time_frames,
                "screen_time_seconds": round(screen_time_seconds, 2),
                "first_frame": frames_list[0] if frames_list else 0,
                "last_frame": frames_list[-1] if frames_list else 0,
            }
        
        # Step 6: Build final response
        return VideoResultsResponse(
            video=video,                        # VideoResponse (converted automatically)
            total_detections=len(detections),   
            unique_brands=len(brands_final),
            brands=brands_final,                # Dict with stats per brand
            detections_by_frame=detections_by_frame,
            processing_time_seconds=None,       # Placeholder
            confidence_threshold=video.confidence_threshold or CONFIDENCE_THRESHOLD,
            iou_threshold=IOU_THRESHOLD,        # We don't store IOU in DB yet, so use default
            fps_sample=1 
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get results error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get results")

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """
    Get Celery task status (for frontend progress tracking)
    """
    from celery.result import AsyncResult
    
    task = AsyncResult(task_id)
    
    return {
        "task_id": task_id,
        "status": task.status,  # PENDING, PROCESSING, SUCCESS, FAILURE
        "progress": task.info if task.status == "PROCESSING" else None,
        "result": task.result if task.successful() else None,
        "error": str(task.info) if task.failed() else None
    }

# MAIN
if __name__ == "__main__":
    import uvicorn
    
    # Start Uvicorn server (ASGI server)
    # ASGI >> Asynchronous Server Gateway Interface
    
    uvicorn.run(
        app,                # The FastAPI application
        host=API_HOST,      # Host, listens on all IPs
        port=API_PORT,      # Port
        reload=API_RELOAD,  # Configurable via API_RELOAD env var (dev mode only)
    )
    
    