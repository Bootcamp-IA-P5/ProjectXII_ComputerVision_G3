"""
Database package for storing detection results

Provides SQLAlchemy models, database connection management,
and repository functions for persisting video detection data.
"""

from src.database.database import get_engine, get_session, get_db_session, init_db
from src.database.models import Base, Video, Brand, Detection, VideoBrandStats
from src.database.repository import DetectionRepository

__all__ = [
    "get_engine",
    "get_session",
    "get_db_session",
    "init_db",
    "Base",
    "Video",
    "Brand",
    "Detection",
    "VideoBrandStats",
    "DetectionRepository",
]

