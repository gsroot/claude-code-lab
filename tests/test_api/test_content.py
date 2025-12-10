"""Tests for content API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from src.api.main import app
from src.models.content import ContentResponse, ContentStatus, ContentRequest, ContentType


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_content_request():
    """Sample content request payload."""
    return {
        "topic": "Test topic for content generation",
        "content_type": "blog_post",
        "tone": "professional",
        "language": "en",
        "word_count": 1000,
    }


class TestHealthEndpoints:
    """Test health and root endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "name" in data
        assert data["name"] == "ContentForge AI"
        assert "version" in data

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestContentEndpoints:
    """Test content generation endpoints."""

    def test_list_content_empty(self, client):
        """Test listing content when empty."""
        response = client.get("/api/v1/content")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_nonexistent_content(self, client):
        """Test getting non-existent content returns 404."""
        response = client.get("/api/v1/content/nonexistent-id")
        assert response.status_code == 404

    def test_delete_nonexistent_content(self, client):
        """Test deleting non-existent content returns 404."""
        response = client.delete("/api/v1/content/nonexistent-id")
        assert response.status_code == 404

    @patch("src.api.routes.content.generate_content")
    def test_create_content_validation(self, mock_generate, client, sample_content_request):
        """Test content creation validates input."""
        # Test with invalid topic (too short)
        invalid_request = {**sample_content_request, "topic": "hi"}
        response = client.post("/api/v1/content/generate", json=invalid_request)
        assert response.status_code == 422  # Validation error

    @patch("src.api.routes.content.generate_content")
    def test_async_content_generation(self, mock_generate, client, sample_content_request):
        """Test async content generation returns content_id."""
        response = client.post(
            "/api/v1/content/generate/async",
            json=sample_content_request,
        )
        assert response.status_code == 200
        data = response.json()
        assert "content_id" in data
        assert data["status"] == "processing"


class TestContentModels:
    """Test content model validation."""

    def test_content_request_defaults(self):
        """Test ContentRequest has sensible defaults."""
        request = ContentRequest(topic="Test topic here")
        assert request.content_type == ContentType.BLOG_POST
        assert request.tone == "professional"
        assert request.language == "en"
        assert request.word_count == 1500

    def test_content_request_validation(self):
        """Test ContentRequest validation."""
        with pytest.raises(ValueError):
            ContentRequest(topic="hi")  # Too short

        with pytest.raises(ValueError):
            ContentRequest(topic="Valid topic", word_count=50)  # Too few words
