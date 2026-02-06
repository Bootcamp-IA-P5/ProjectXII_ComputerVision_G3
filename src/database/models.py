"""
SQLAlchemy ORM Models for Detection Results

Defines the database schema for storing video processing results,
including videos, brands, individual detections, and aggregated statistics.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models"""
    pass


class Video(Base):
    """
    Represents a processed video file
    
    Stores video metadata and links to all detections found in the video.
    """
    __tablename__ = "videos"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    filepath: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    
    # Video metadata
    total_frames: Mapped[int] = mapped_column(Integer, nullable=False)
    processed_frames: Mapped[int] = mapped_column(Integer, nullable=False)
    fps: Mapped[float] = mapped_column(Float, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    frame_width: Mapped[int] = mapped_column(Integer, nullable=False)
    frame_height: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Processing metadata
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confidence_threshold: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    detections: Mapped[List["Detection"]] = relationship(
        "Detection", back_populates="video", cascade="all, delete-orphan"
    )
    brand_stats: Mapped[List["VideoBrandStats"]] = relationship(
        "VideoBrandStats", back_populates="video", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Video(id={self.id}, filename='{self.filename}')>"


class Brand(Base):
    """
    Represents a unique brand/logo class
    
    Each brand corresponds to a YOLO class (e.g., "Nike", "Adidas").
    Brands are created once and referenced by detections.
    """
    __tablename__ = "brands"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    class_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    
    # Relationships
    detections: Mapped[List["Detection"]] = relationship(
        "Detection", back_populates="brand"
    )
    video_stats: Mapped[List["VideoBrandStats"]] = relationship(
        "VideoBrandStats", back_populates="brand"
    )
    
    def __repr__(self) -> str:
        return f"<Brand(id={self.id}, name='{self.name}')>"


class Detection(Base):
    """
    Represents a single logo detection in a video frame
    
    Stores the bounding box coordinates (both normalized and pixel),
    confidence score, and links to the video and brand.
    """
    __tablename__ = "detections"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False
    )
    brand_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("brands.id"), nullable=False
    )
    
    # Frame info
    frame_number: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Normalized bounding box (0-1)
    x_center: Mapped[float] = mapped_column(Float, nullable=False)
    y_center: Mapped[float] = mapped_column(Float, nullable=False)
    width: Mapped[float] = mapped_column(Float, nullable=False)
    height: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Pixel bounding box
    x1: Mapped[int] = mapped_column(Integer, nullable=False)
    y1: Mapped[int] = mapped_column(Integer, nullable=False)
    x2: Mapped[int] = mapped_column(Integer, nullable=False)
    y2: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Relationships
    video: Mapped["Video"] = relationship("Video", back_populates="detections")
    brand: Mapped["Brand"] = relationship("Brand", back_populates="detections")
    
    # Indexes for common queries
    __table_args__ = (
        Index("ix_detections_video_frame", "video_id", "frame_number"),
        Index("ix_detections_brand", "brand_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Detection(id={self.id}, brand_id={self.brand_id}, frame={self.frame_number})>"


class VideoBrandStats(Base):
    """
    Aggregated statistics for a brand within a specific video
    
    Pre-computed stats for efficient querying of brand screen time
    and detection counts without scanning all detections.
    """
    __tablename__ = "video_brand_stats"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False
    )
    brand_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("brands.id"), nullable=False
    )
    
    # Aggregated metrics
    detection_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    screen_time_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    screen_time_frames: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Frame range
    first_frame: Mapped[int] = mapped_column(Integer, nullable=False)
    last_frame: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Relationships
    video: Mapped["Video"] = relationship("Video", back_populates="brand_stats")
    brand: Mapped["Brand"] = relationship("Brand", back_populates="video_stats")
    
    # Unique constraint: one stats record per video-brand pair
    __table_args__ = (
        UniqueConstraint("video_id", "brand_id", name="uq_video_brand"),
    )
    
    def __repr__(self) -> str:
        return f"<VideoBrandStats(video_id={self.video_id}, brand_id={self.brand_id})>"
