"""
Unit tests for YOLOInference class
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


class TestYOLOInferenceInit:
    """Tests for YOLOInference initialization"""
    
    @pytest.mark.unit
    def test_init_raises_on_missing_model(self, temp_dir):
        """Test that initialization raises error when model file doesn't exist"""
        from src.model_inference.yolo_inference import YOLOInference
        
        with pytest.raises(FileNotFoundError):
            YOLOInference(model_path=str(temp_dir / "nonexistent_model.pt"))


class TestYOLOInferencePredict:
    """Tests for prediction functionality"""
    
    @pytest.mark.unit
    @patch('src.model_inference.yolo_inference.YOLO')
    def test_predict_returns_expected_format(self, mock_yolo_class, temp_dir):
        """Test that predict returns correctly formatted results"""
        # Create a mock model file
        model_path = temp_dir / "test_model.pt"
        model_path.write_bytes(b"mock model")
        
        # Setup mock YOLO model
        mock_model = MagicMock()
        mock_yolo_class.return_value = mock_model
        
        # Mock prediction result
        mock_box = MagicMock()
        mock_box.xyxy = [MagicMock()]
        mock_box.xyxy[0].cpu.return_value.numpy.return_value = np.array([100, 100, 200, 200])
        mock_box.conf = [MagicMock()]
        mock_box.conf[0].cpu.return_value.numpy.return_value = np.array(0.95)
        mock_box.cls = [MagicMock()]
        mock_box.cls[0].cpu.return_value.numpy.return_value = np.array(0)
        
        mock_result = MagicMock()
        mock_result.boxes = [mock_box]
        mock_model.predict.return_value = [mock_result]
        mock_model.names = {0: "Nike"}
        
        from src.model_inference.yolo_inference import YOLOInference
        
        inference = YOLOInference(model_path=str(model_path))
        
        # Create a test image
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        result = inference.predict(test_image)
        
        # Verify result structure
        assert "detections" in result
        assert "image_shape" in result
        assert isinstance(result["detections"], list)
    
    @pytest.mark.unit
    @patch('src.model_inference.yolo_inference.YOLO')
    def test_predict_empty_results(self, mock_yolo_class, temp_dir):
        """Test prediction with no detections"""
        model_path = temp_dir / "test_model.pt"
        model_path.write_bytes(b"mock model")
        
        mock_model = MagicMock()
        mock_yolo_class.return_value = mock_model
        
        # Mock empty result
        mock_result = MagicMock()
        mock_result.boxes = None
        mock_model.predict.return_value = [mock_result]
        mock_model.names = {}
        
        from src.model_inference.yolo_inference import YOLOInference
        
        inference = YOLOInference(model_path=str(model_path))
        
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        result = inference.predict(test_image)
        
        assert result["detections"] == []


class TestYOLOInferenceClassCount:
    """Tests for class counting functionality"""
    
    @pytest.mark.unit
    def test_get_class_count_empty(self):
        """Test class count with empty detections"""
        # We need to mock the model loading to test this
        with patch('src.model_inference.yolo_inference.YOLO'):
            with patch.object(Path, 'exists', return_value=True):
                from src.model_inference.yolo_inference import YOLOInference
                
                # Create instance with mocked model
                inference = YOLOInference.__new__(YOLOInference)
                inference.model_path = Path("fake.pt")
                
                result = inference.get_class_count([])
                assert result == {}
    
    @pytest.mark.unit
    def test_get_class_count_multiple_classes(self):
        """Test class count with multiple detections"""
        with patch('src.model_inference.yolo_inference.YOLO'):
            with patch.object(Path, 'exists', return_value=True):
                from src.model_inference.yolo_inference import YOLOInference
                
                inference = YOLOInference.__new__(YOLOInference)
                inference.model_path = Path("fake.pt")
                
                detections = [
                    {"class_name": "Nike", "confidence": 0.9},
                    {"class_name": "Adidas", "confidence": 0.85},
                    {"class_name": "Nike", "confidence": 0.8},
                    {"class_name": "Nike", "confidence": 0.7},
                ]
                
                result = inference.get_class_count(detections)
                
                assert result["Nike"] == 3
                assert result["Adidas"] == 1
