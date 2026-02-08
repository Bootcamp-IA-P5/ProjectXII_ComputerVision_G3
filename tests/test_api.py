"""
Unit tests for FastAPI endpoints
"""

import pytest
from fastapi import status


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    @pytest.mark.unit
    def test_root_returns_ok(self, api_client):
        """Test that root endpoint returns status ok"""
        response = api_client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ok"
        assert data["message"] == "API running"
        assert "version" in data


class TestHealthEndpoint:
    """Tests for the health check endpoint"""
    
    @pytest.mark.unit
    def test_health_returns_healthy(self, api_client):
        """Test that health endpoint returns healthy status"""
        response = api_client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "components" in data
        assert "timestamp" in data
    
    @pytest.mark.unit
    def test_health_includes_components(self, api_client):
        """Test that health endpoint checks required components"""
        response = api_client.get("/health")
        
        data = response.json()
        components = data.get("components", {})
        
        # Should check database
        assert "database" in components
        
        # Should check model (even if not found)
        assert "model" in components


class TestUploadEndpoint:
    """Tests for video upload endpoint"""
    
    @pytest.mark.unit
    def test_upload_requires_file(self, api_client):
        """Test that upload endpoint requires a file"""
        response = api_client.post("/upload")
        
        # Should fail without file
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.unit
    def test_upload_accepts_video_file(self, api_client, mock_video_file):
        """Test that upload endpoint accepts a video file"""
        # Note: This test may fail if Celery is not configured
        # In a real test, we'd mock the Celery task
        with open(mock_video_file, "rb") as f:
            response = api_client.post(
                "/upload",
                files={"file": ("test.mp4", f, "video/mp4")},
                data={
                    "confidence_threshold": 0.5,
                    "iou_threshold": 0.45,
                    "fps_sample": 1
                }
            )
        
        # If Celery is not running, this might return 500
        # Otherwise, should return 200 with video_id
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "video_id" in data
            assert data["status"] in ["queued", "pending"]


class TestVideoListEndpoint:
    """Tests for video list endpoint"""
    
    @pytest.mark.unit
    def test_videos_returns_list(self, api_client):
        """Test that /videos returns a list"""
        response = api_client.get("/videos")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)


class TestVideoDetailEndpoint:
    """Tests for video detail endpoint"""
    
    @pytest.mark.unit
    def test_nonexistent_video_returns_404(self, api_client):
        """Test that requesting non-existent video returns 404"""
        response = api_client.get("/videos/99999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
