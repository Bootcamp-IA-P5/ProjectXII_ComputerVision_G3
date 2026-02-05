"""
Database initialization and connection management
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from src.config import DATABASE_URL
from src.database.models import Base

logger = logging.getLogger(__name__)

# Create engine with appropriate pool settings
# Use NullPool for connection issues with remote databases (Supabase)
engine = create_engine(
    DATABASE_URL,
    echo=False,
    poolclass=NullPool if "postgresql" in DATABASE_URL else None,
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def init_db() -> None:
    """
    Create all database tables

    This function creates all tables defined in the models.
    Safe to call multiple times (idempotent).
    """
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified successfully")


def get_db() -> Session:
    """
    Get database session for dependency injection

    Yields:
        SQLAlchemy session object

    Example:
        @app.get("/videos")
        def list_videos(db: Session = Depends(get_db)):
            return db.query(Video).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def close_db() -> None:
    """Close all database connections"""
    engine.dispose()
    logger.info("Database connections closed")