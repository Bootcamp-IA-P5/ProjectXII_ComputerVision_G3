"""
Database Connection Management

Provides SQLAlchemy engine and session factory for PostgreSQL/SQLite connections.
Supports both production (PostgreSQL) and development (SQLite) modes.
"""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.config import DATABASE_URL
from src.database.models import Base

logger = logging.getLogger(__name__)

# Global engine and session factory (lazy initialization)
_engine = None
_SessionLocal = None


def get_engine(database_url: str = None):
    """
    Get or create SQLAlchemy engine
    
    Args:
        database_url: Override DATABASE_URL from config (optional)
        
    Returns:
        SQLAlchemy Engine instance
        
    Note:
        Automatically detects Supabase/cloud PostgreSQL and enables SSL.
    """
    global _engine
    
    if _engine is None:
        url = database_url or DATABASE_URL
        
        # Configure engine based on database type
        if url.startswith("sqlite"):
            # SQLite-specific settings
            _engine = create_engine(
                url,
                connect_args={"check_same_thread": False},
                echo=False,
            )
        else:
            # PostgreSQL settings
            connect_args = {}
            
            # Enable SSL for cloud databases (Supabase, AWS RDS, etc.)
            # Supabase URLs contain 'supabase' or use pooler.supabase.com
            if "supabase" in url or "pooler" in url or "aws" in url:
                connect_args["sslmode"] = "require"
                logger.info("SSL mode enabled for cloud database")
            
            _engine = create_engine(
                url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=300,  # Recycle connections after 5 min (good for cloud)
                echo=False,
                connect_args=connect_args,
            )
        
        # Log connection (hide password)
        safe_url = url.split('@')[-1] if '@' in url else url
        logger.info(f"Database engine created: {safe_url}")
    
    return _engine


def get_session_factory():
    """
    Get or create session factory
    
    Returns:
        SQLAlchemy sessionmaker instance
    """
    global _SessionLocal
    
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,  # Prevent expiration after commit (fixes PostgreSQL issues)
            bind=engine,
        )
    
    return _SessionLocal


def get_session() -> Session:
    """
    Create a new database session
    
    Returns:
        SQLAlchemy Session instance
        
    Note:
        Caller is responsible for closing the session.
        Prefer using get_db_session() context manager instead.
    """
    SessionLocal = get_session_factory()
    return SessionLocal()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions
    
    Automatically handles commit on success and rollback on error.
    
    Usage:
        with get_db_session() as session:
            session.add(my_object)
            # Auto-commits on exit, or rolls back on exception
    
    Yields:
        SQLAlchemy Session instance
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def init_db(database_url: str = None) -> None:
    """
    Initialize database by creating all tables
    
    Args:
        database_url: Override DATABASE_URL from config (optional)
        
    Creates all tables defined in models.py if they don't exist.
    Safe to call multiple times.
    """
    engine = get_engine(database_url)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")


def drop_all_tables(confirm: bool = False) -> None:
    """
    Drop all tables (USE WITH CAUTION)
    
    Args:
        confirm: Must be True to actually drop tables
        
    Raises:
        ValueError: If confirm is not True
    """
    if not confirm:
        raise ValueError("Must pass confirm=True to drop all tables")
    
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped!")


def reset_connection() -> None:
    """
    Reset the global engine and session factory
    
    Useful for testing or when changing database URLs.
    """
    global _engine, _SessionLocal
    
    if _engine:
        _engine.dispose()
    
    _engine = None
    _SessionLocal = None
    logger.info("Database connection reset")
