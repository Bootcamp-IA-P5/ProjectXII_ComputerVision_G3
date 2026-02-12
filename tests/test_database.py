"""
Unit tests for database models and repository
"""

import pytest
from datetime import datetime


class TestVideoModel:
    """Tests for Video ORM model"""
    
    @pytest.mark.unit
    def test_video_creation(self, test_db_session):
        """Test creating a Video record"""
        from src.database.models import Video
        
        video = Video(
            filename="test_video.mp4",
            filepath="/path/to/test_video.mp4",
            total_frames=300,
            processed_frames=150,
            fps=30.0,
            duration_seconds=10.0,
            frame_width=1920,
            frame_height=1080,
        )
        
        test_db_session.add(video)
        test_db_session.commit()
        
        assert video.id is not None
        assert video.filename == "test_video.mp4"
        assert video.created_at is not None
    
    @pytest.mark.unit
    def test_video_repr(self, test_db_session):
        """Test Video string representation"""
        from src.database.models import Video
        
        video = Video(
            filename="test.mp4",
            filepath="/path/test.mp4",
            total_frames=100,
            processed_frames=100,
            fps=30.0,
            duration_seconds=3.33,
            frame_width=1920,
            frame_height=1080,
        )
        
        test_db_session.add(video)
        test_db_session.commit()
        
        assert "test.mp4" in repr(video)


class TestBrandModel:
    """Tests for Brand ORM model"""
    
    @pytest.mark.unit
    def test_brand_creation(self, test_db_session):
        """Test creating a Brand record"""
        from src.database.models import Brand
        
        brand = Brand(name="Nike", class_id=0)
        
        test_db_session.add(brand)
        test_db_session.commit()
        
        assert brand.id is not None
        assert brand.name == "Nike"
        assert brand.class_id == 0
    
    @pytest.mark.unit
    def test_brand_unique_name(self, test_db_session):
        """Test that brand names must be unique"""
        from src.database.models import Brand
        from sqlalchemy.exc import IntegrityError
        
        brand1 = Brand(name="Adidas", class_id=1)
        brand2 = Brand(name="Adidas", class_id=2)
        
        test_db_session.add(brand1)
        test_db_session.commit()
        
        test_db_session.add(brand2)
        
        with pytest.raises(IntegrityError):
            test_db_session.commit()


class TestDetectionModel:
    """Tests for Detection ORM model"""
    
    @pytest.mark.unit
    def test_detection_creation(self, test_db_session):
        """Test creating a Detection record with relationships"""
        from src.database.models import Video, Brand, Detection
        
        # Create video and brand first
        video = Video(
            filename="test.mp4",
            filepath="/path/test.mp4",
            total_frames=100,
            processed_frames=100,
            fps=30.0,
            duration_seconds=3.33,
            frame_width=1920,
            frame_height=1080,
        )
        brand = Brand(name="Puma", class_id=2)
        
        test_db_session.add_all([video, brand])
        test_db_session.commit()
        
        # Create detection
        detection = Detection(
            video_id=video.id,
            brand_id=brand.id,
            frame_number=10,
            confidence=0.95,
            x_center=0.5,
            y_center=0.5,
            width=0.2,
            height=0.1,
            x1=400,
            y1=450,
            x2=600,
            y2=550,
        )
        
        test_db_session.add(detection)
        test_db_session.commit()
        
        assert detection.id is not None
        assert detection.video.filename == "test.mp4"
        assert detection.brand.name == "Puma"


class TestVideoBrandStatsModel:
    """Tests for VideoBrandStats ORM model"""
    
    @pytest.mark.unit
    def test_video_brand_stats_creation(self, test_db_session):
        """Test creating aggregated brand statistics"""
        from src.database.models import Video, Brand, VideoBrandStats
        
        video = Video(
            filename="stats_test.mp4",
            filepath="/path/stats_test.mp4",
            total_frames=1000,
            processed_frames=500,
            fps=30.0,
            duration_seconds=33.33,
            frame_width=1920,
            frame_height=1080,
        )
        brand = Brand(name="Apple", class_id=3)
        
        test_db_session.add_all([video, brand])
        test_db_session.commit()
        
        stats = VideoBrandStats(
            video_id=video.id,
            brand_id=brand.id,
            detection_count=150,
            avg_confidence=0.92,
            screen_time_seconds=5.0,
            screen_time_frames=150,
            first_frame=10,
            last_frame=500,
        )
        
        test_db_session.add(stats)
        test_db_session.commit()
        
        assert stats.id is not None
        assert stats.video.filename == "stats_test.mp4"
        assert stats.brand.name == "Apple"


class TestCascadeDelete:
    """Tests for cascade delete behavior"""
    
    @pytest.mark.unit
    def test_video_delete_cascades_to_detections(self, test_db_session):
        """Test that deleting a video also deletes its detections"""
        from src.database.models import Video, Brand, Detection
        
        video = Video(
            filename="cascade_test.mp4",
            filepath="/path/cascade_test.mp4",
            total_frames=100,
            processed_frames=100,
            fps=30.0,
            duration_seconds=3.33,
            frame_width=1920,
            frame_height=1080,
        )
        brand = Brand(name="Google", class_id=4)
        
        test_db_session.add_all([video, brand])
        test_db_session.commit()
        
        detection = Detection(
            video_id=video.id,
            brand_id=brand.id,
            frame_number=0,
            confidence=0.9,
            x_center=0.5,
            y_center=0.5,
            width=0.2,
            height=0.1,
            x1=400,
            y1=450,
            x2=600,
            y2=550,
        )
        
        test_db_session.add(detection)
        test_db_session.commit()
        
        detection_id = detection.id
        
        # Delete video
        test_db_session.delete(video)
        test_db_session.commit()
        
        # Detection should be gone
        remaining = test_db_session.query(Detection).filter(
            Detection.id == detection_id
        ).first()
        
        assert remaining is None
