"""
Detection Repository

Data access layer for saving and querying video detection results.
Provides high-level methods for persisting VideoProcessor output.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.database.models import Video, Brand, Detection, VideoBrandStats
from src.database.database import get_db_session

logger = logging.getLogger(__name__)


class DetectionRepository:
    """
    Repository for managing detection data persistence
    
    Handles saving complete video processing results and provides
    query methods for analytics.
    """
    
    def __init__(self, session: Session = None):
        """
        Initialize repository
        
        Args:
            session: Optional SQLAlchemy session. If not provided,
                    methods will create their own sessions.
        """
        self._session = session
    
    def save_video_result(
        self,
        result: Dict[str, Any],
        model_name: str = None,
        confidence_threshold: float = None,
        replace_existing: bool = True,
    ) -> Video:
        """
        Save complete video processing result to database
        
        Takes the output from VideoProcessor.process_video() and persists
        all data including video metadata, detections, and aggregated stats.
        
        Args:
            result: Output dictionary from VideoProcessor.process_video()
            model_name: Name of the YOLO model used (optional)
            confidence_threshold: Confidence threshold used (optional)
            replace_existing: If True, delete existing video with same filepath first
            
        Returns:
            Created Video ORM object with ID
            
        Raises:
            ValueError: If result contains an error or missing required fields
        """
        if "error" in result:
            raise ValueError(f"Cannot save error result: {result['error']}")
        
        filepath = result["video_path"]
        
        with get_db_session() as session:
            # Check for existing video with same filepath
            video = session.query(Video).filter(Video.filepath == filepath).first()
            
            if video:
                logger.info(f"Updating existing video record: {video.filename} (ID={video.id})")
                # Update metadata
                video.total_frames = result["total_frames"]
                video.processed_frames = result["processed_frames"]
                video.fps = result["fps"]
                video.duration_seconds = result["duration_seconds"]
                video.frame_height = result["frame_dimensions"][0]
                video.frame_width = result["frame_dimensions"][1]
                video.model_name = model_name
                video.confidence_threshold = confidence_threshold
                video.processed_at = datetime.utcnow()
                
                # Clear existing detections/stats if replace_existing is True
                if replace_existing:
                    video.detections = []
                    video.brand_stats = []
            else:
                # Create video record
                video = Video(
                    filename=filepath.split("/")[-1].split("\\")[-1],
                    filepath=filepath,
                    total_frames=result["total_frames"],
                    processed_frames=result["processed_frames"],
                    fps=result["fps"],
                    duration_seconds=result["duration_seconds"],
                    frame_height=result["frame_dimensions"][0],
                    frame_width=result["frame_dimensions"][1],
                    model_name=model_name,
                    confidence_threshold=confidence_threshold,
                    processed_at=datetime.utcnow(),
                )
                session.add(video)
            
            session.flush()  # Get video.id
            
            # Process detections by frame
            detections_by_frame = result.get("detections_by_frame", {})
            stats = result.get("statistics", {})
            
            # Cache for brand lookup/creation
            brand_cache: Dict[str, Brand] = {}
            
            # Save individual detections
            for frame_idx, frame_detections in detections_by_frame.items():
                for det in frame_detections:
                    # Get or create brand
                    brand_name = det["class_name"]
                    if brand_name not in brand_cache:
                        brand = self._get_or_create_brand(
                            session, brand_name, det["class_id"]
                        )
                        brand_cache[brand_name] = brand
                    else:
                        brand = brand_cache[brand_name]
                    
                    # Create detection record
                    bbox_norm = det["bbox_normalized"]
                    bbox_pixel = det["bbox_pixel"]
                    
                    detection = Detection(
                        video_id=video.id,
                        brand_id=brand.id,
                        frame_number=int(frame_idx),
                        confidence=det["confidence"],
                        x_center=bbox_norm[0],
                        y_center=bbox_norm[1],
                        width=bbox_norm[2],
                        height=bbox_norm[3],
                        x1=bbox_pixel[0],
                        y1=bbox_pixel[1],
                        x2=bbox_pixel[2],
                        y2=bbox_pixel[3],
                    )
                    session.add(detection)
            
            # Save aggregated stats per brand
            by_class = stats.get("by_class", {})
            for brand_name, class_stats in by_class.items():
                brand = brand_cache.get(brand_name)
                if not brand:
                    continue
                
                # Calculate screen time in seconds
                screen_time_frames = class_stats.get("screen_time_frames", 0)
                fps = result["fps"] if result["fps"] > 0 else 1
                screen_time_seconds = screen_time_frames / fps
                
                video_brand_stats = VideoBrandStats(
                    video_id=video.id,
                    brand_id=brand.id,
                    detection_count=class_stats.get("count", 0),
                    avg_confidence=class_stats.get("avg_confidence", 0.0),
                    screen_time_seconds=screen_time_seconds,
                    screen_time_frames=screen_time_frames,
                    first_frame=class_stats.get("first_frame", 0),
                    last_frame=class_stats.get("last_frame", 0),
                )
                session.add(video_brand_stats)
            
            logger.info(
                f"Saved video '{video.filename}' with "
                f"{len(brand_cache)} brands, "
                f"{stats.get('total_detections', 0)} detections"
            )
            
            # Store data before session closes to avoid detached instance issues
            from collections import namedtuple
            SavedVideo = namedtuple('SavedVideo', ['id', 'filename'])
            saved = SavedVideo(id=video.id, filename=video.filename)
        
        return saved
    
    def _get_or_create_brand(
        self, session: Session, name: str, class_id: int
    ) -> Brand:
        """
        Get existing brand or create new one
        
        Args:
            session: Database session
            name: Brand name
            class_id: YOLO class ID
            
        Returns:
            Brand ORM object
        """
        brand = session.query(Brand).filter(Brand.name == name).first()
        if not brand:
            brand = Brand(name=name, class_id=class_id)
            session.add(brand)
            session.flush()
        return brand
    
    def get_video_by_id(self, video_id: int) -> Optional[Video]:
        """
        Get video by ID with all relationships loaded
        
        Args:
            video_id: Video primary key
            
        Returns:
            Video object or None if not found
        """
        with get_db_session() as session:
            video = session.query(Video).filter(Video.id == video_id).first()
            if video:
                # Eager load relationships
                _ = video.detections
                _ = video.brand_stats
            return video
    
    def get_video_by_filepath(self, filepath: str) -> Optional[Video]:
        """
        Get video by file path
        
        Args:
            filepath: Full path to video file
            
        Returns:
            Video object or None if not found
        """
        with get_db_session() as session:
            return session.query(Video).filter(Video.filepath == filepath).first()
    
    def get_all_videos(self, limit: int = 100, offset: int = 0) -> List[Video]:
        """
        Get all processed videos
        
        Args:
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            List of Video objects
        """
        with get_db_session() as session:
            return (
                session.query(Video)
                .order_by(Video.processed_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
    
    def get_brand_rankings(
        self, video_id: int = None, top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get brand rankings by total screen time
        
        Args:
            video_id: Filter to specific video (optional)
            top_n: Number of top brands to return
            
        Returns:
            List of dicts with brand name, total screen time, detection count
        """
        with get_db_session() as session:
            query = (
                session.query(
                    Brand.name,
                    func.sum(VideoBrandStats.screen_time_seconds).label("total_screen_time"),
                    func.sum(VideoBrandStats.detection_count).label("total_detections"),
                    func.avg(VideoBrandStats.avg_confidence).label("avg_confidence"),
                )
                .join(VideoBrandStats, Brand.id == VideoBrandStats.brand_id)
            )
            
            if video_id:
                query = query.filter(VideoBrandStats.video_id == video_id)
            
            results = (
                query.group_by(Brand.name)
                .order_by(func.sum(VideoBrandStats.screen_time_seconds).desc())
                .limit(top_n)
                .all()
            )
            
            return [
                {
                    "brand": r.name,
                    "total_screen_time_seconds": float(r.total_screen_time or 0),
                    "total_detections": int(r.total_detections or 0),
                    "avg_confidence": float(r.avg_confidence or 0),
                }
                for r in results
            ]
    
    def get_video_summary(self, video_id: int) -> Optional[Dict[str, Any]]:
        """
        Get summary statistics for a video
        
        Args:
            video_id: Video primary key
            
        Returns:
            Summary dict or None if video not found
        """
        with get_db_session() as session:
            video = session.query(Video).filter(Video.id == video_id).first()
            if not video:
                return None
            
            # Get aggregated stats
            stats = (
                session.query(
                    func.count(VideoBrandStats.id).label("unique_brands"),
                    func.sum(VideoBrandStats.detection_count).label("total_detections"),
                    func.sum(VideoBrandStats.screen_time_seconds).label("total_brand_time"),
                )
                .filter(VideoBrandStats.video_id == video_id)
                .first()
            )
            
            return {
                "video_id": video.id,
                "filename": video.filename,
                "duration_seconds": video.duration_seconds,
                "total_frames": video.total_frames,
                "processed_frames": video.processed_frames,
                "unique_brands": stats.unique_brands or 0,
                "total_detections": int(stats.total_detections or 0),
                "total_brand_screen_time": float(stats.total_brand_time or 0),
                "processed_at": video.processed_at.isoformat() if video.processed_at else None,
            }
    
    def delete_video(self, video_id: int) -> bool:
        """
        Delete a video and all associated data
        
        Args:
            video_id: Video primary key
            
        Returns:
            True if deleted, False if not found
        """
        with get_db_session() as session:
            video = session.query(Video).filter(Video.id == video_id).first()
            if video:
                session.delete(video)
                logger.info(f"Deleted video ID {video_id}")
                return True
            return False
