"""
Unit tests for VideoProcessor class
"""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path


class TestVideoProcessorInit:
    """Tests for VideoProcessor initialization"""
    
    @pytest.mark.unit
    def test_init_with_defaults(self):
        """Test VideoProcessor initialization with default parameters"""
        mock_model = Mock()
        
        from src.video_processor.video_processor import VideoProcessor
        
        processor = VideoProcessor(model=mock_model)
        
        assert processor.model == mock_model
        assert processor.fps_sample == 1  # DEFAULT_FPS_SAMPLE
        assert processor.cap is None
        assert processor.total_frames == 0
    
    @pytest.mark.unit
    def test_init_with_custom_fps_sample(self):
        """Test VideoProcessor with custom fps_sample"""
        mock_model = Mock()
        
        from src.video_processor.video_processor import VideoProcessor
        
        processor = VideoProcessor(model=mock_model, fps_sample=5)
        
        assert processor.fps_sample == 5


class TestVideoProcessorLoadVideo:
    """Tests for video loading functionality"""
    
    @pytest.mark.unit
    def test_load_nonexistent_video_returns_false(self, temp_dir):
        """Test loading a non-existent video file"""
        mock_model = Mock()
        
        from src.video_processor.video_processor import VideoProcessor
        
        processor = VideoProcessor(model=mock_model)
        result = processor.load_video(str(temp_dir / "nonexistent.mp4"))
        
        assert result is False
    
    @pytest.mark.unit
    def test_load_unsupported_format_returns_false(self, temp_dir):
        """Test loading a file with unsupported extension"""
        mock_model = Mock()
        
        from src.video_processor.video_processor import VideoProcessor
        
        # Create a file with unsupported extension
        unsupported_file = temp_dir / "test.xyz"
        unsupported_file.write_bytes(b"not a video")
        
        processor = VideoProcessor(model=mock_model)
        result = processor.load_video(str(unsupported_file))
        
        assert result is False


class TestVideoProcessorExtractFrames:
    """Tests for frame extraction"""
    
    @pytest.mark.unit
    def test_extract_frames_without_loaded_video_returns_empty(self):
        """Test extracting frames without loading a video first"""
        mock_model = Mock()
        
        from src.video_processor.video_processor import VideoProcessor
        
        processor = VideoProcessor(model=mock_model)
        frames = processor.extract_frames()
        
        assert frames == []
    
    @pytest.mark.unit
    def test_extract_frames_with_invalid_fps_sample_returns_empty(self):
        """Test that invalid fps_sample values return empty list"""
        mock_model = Mock()
        
        from src.video_processor.video_processor import VideoProcessor
        
        processor = VideoProcessor(model=mock_model)
        processor.cap = Mock()  # Fake that video is loaded
        
        # Test with 0
        frames = processor.extract_frames(fps_sample=0)
        assert frames == []
        
        # Test with negative
        frames = processor.extract_frames(fps_sample=-1)
        assert frames == []


class TestVideoProcessorStatistics:
    """Tests for statistics calculation"""
    
    @pytest.mark.unit
    def test_calculate_statistics_empty_detections(self):
        """Test statistics calculation with empty detections"""
        mock_model = Mock()
        
        from src.video_processor.video_processor import VideoProcessor
        
        processor = VideoProcessor(model=mock_model)
        stats = processor._calculate_statistics({})
        
        assert stats["total_detections"] == 0
        assert stats["unique_classes"] == 0
        assert stats["by_class"] == {}
    
    @pytest.mark.unit
    def test_calculate_statistics_with_detections(self, sample_detection):
        """Test statistics calculation with sample detections"""
        mock_model = Mock()
        
        from src.video_processor.video_processor import VideoProcessor
        
        processor = VideoProcessor(model=mock_model)
        
        detections = {
            0: [sample_detection],
            10: [sample_detection],
            20: [sample_detection],
        }
        
        stats = processor._calculate_statistics(detections)
        
        assert stats["total_detections"] == 3
        assert stats["unique_classes"] == 1
        assert "Nike" in stats["by_class"]
        assert stats["by_class"]["Nike"]["count"] == 3
        assert stats["by_class"]["Nike"]["avg_confidence"] == pytest.approx(0.92)


class TestVideoProcessorContextManager:
    """Tests for context manager functionality"""
    
    @pytest.mark.unit
    def test_context_manager_closes_video(self):
        """Test that context manager properly closes video"""
        mock_model = Mock()
        
        from src.video_processor.video_processor import VideoProcessor
        
        with VideoProcessor(model=mock_model) as processor:
            processor.cap = Mock()
        
        # After exiting context, cap should be released
        processor.cap.release.assert_called_once()
