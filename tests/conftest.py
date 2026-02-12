"""
Pytest configuration and fixtures for ProjectXII tests
"""

import pytest
import asyncio
from pathlib import Path
from typing import Generator
import tempfile
import shutil

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# Async Configuration
# =============================================================================
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Test Data Fixtures
# =============================================================================
@pytest.fixture
def sample_detection():
    """Sample detection dictionary matching YOLOInference output format"""
    return {
        "class_id": 0,
        "class_name": "Nike",
        "confidence": 0.92,
        "bbox_normalized": [0.5, 0.5, 0.2, 0.1],
        "bbox_pixel": [400, 450, 600, 550],
    }


@pytest.fixture
def sample_video_result(sample_detection):
    """Sample video processing result matching VideoProcessor output"""
    return {
        "video_path": "/tmp/test_video.mp4",
        "total_frames": 300,
        "processed_frames": 150,
        "fps": 30.0,
        "duration_seconds": 10.0,
        "frame_dimensions": (1080, 1920),
        "detections_by_frame": {
            0: [sample_detection],
            30: [sample_detection],
            60: [sample_detection],
        },
        "statistics": {
            "total_detections": 3,
            "unique_classes": 1,
            "by_class": {
                "Nike": {
                    "count": 3,
                    "avg_confidence": 0.92,
                    "frames_with_detection": [0, 30, 60],
                    "first_frame": 0,
                    "last_frame": 60,
                    "screen_time_frames": 3,
                }
            }
        }
    }


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_video_file(temp_dir) -> Path:
    """Create a mock video file path (doesn't actually contain video data)"""
    video_path = temp_dir / "test_video.mp4"
    video_path.write_bytes(b"mock video content")
    return video_path


# =============================================================================
# Database Fixtures
# =============================================================================
@pytest.fixture
def test_db_session():
    """
    Create a test database session using SQLite in-memory
    
    This avoids needing PostgreSQL for unit tests.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.database.models import Base
    
    # Use SQLite in-memory for fast tests
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    
    yield session
    
    session.close()
    engine.dispose()


# =============================================================================
# API Client Fixtures
# =============================================================================
@pytest.fixture
def api_client():
    """
    Create a test client for FastAPI
    
    Note: Requires httpx to be installed (in requirements-dev.txt)
    """
    from fastapi.testclient import TestClient
    from src.api.main import app
    
    # Override database dependency for tests
    from src.database.init_db import get_db
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.database.models import Base
    
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    
    def override_get_db():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()
    engine.dispose()
