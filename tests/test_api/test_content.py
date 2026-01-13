"""Tests for content API endpoints."""

from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.routes.content import content_storage
from src.models.content import (
    ContentOutline,
    ContentRequest,
    ContentResponse,
    ContentStatus,
    ContentType,
    ResearchResult,
)


@pytest.fixture
def client():
    """Create test client."""
    # Clear storage before each test
    content_storage.clear()
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


@pytest.fixture
def sample_completed_content():
    """Sample completed content for testing."""
    return ContentResponse(
        id="test-content-123",
        status=ContentStatus.COMPLETED,
        request=ContentRequest(
            topic="Test topic for content generation",
            content_type=ContentType.BLOG_POST,
            tone="professional",
            language="en",
            word_count=1000,
        ),
        content="# Test Content\n\nThis is the generated content.",
        outline=ContentOutline(
            title="Test Content Title",
            hook="This is a hook",
            sections=[{"header": "Section 1", "purpose": "Test", "points": ["Point 1"]}],
            conclusion_points=["Conclusion"],
            cta="Call to action",
        ),
        research=ResearchResult(
            key_facts=["Fact 1"],
            statistics=["Stat 1"],
            quotes=["Quote 1"],
            competitor_insights=["Insight 1"],
        ),
        created_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        processing_time_seconds=5.5,
    )


class TestHealthEndpoints:
    """Test health and root endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "name" in data
        assert data["name"] == "Content Mate"
        assert "version" in data
        assert data["status"] == "running"

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
        assert len(response.json()) == 0

    def test_get_nonexistent_content(self, client):
        """Test getting non-existent content returns 404."""
        response = client.get("/api/v1/content/nonexistent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_nonexistent_content(self, client):
        """Test deleting non-existent content returns 404."""
        response = client.delete("/api/v1/content/nonexistent-id")
        assert response.status_code == 404

    def test_get_status_nonexistent_content(self, client):
        """Test getting status of non-existent content returns 404."""
        response = client.get("/api/v1/content/nonexistent-id/status")
        assert response.status_code == 404

    @patch("src.api.routes.content.generate_content")
    def test_create_content_validation_topic_too_short(self, mock_generate, client):
        """Test content creation validates topic length."""
        invalid_request = {"topic": "hi", "content_type": "blog_post"}
        response = client.post("/api/v1/content/generate", json=invalid_request)
        assert response.status_code == 422  # Validation error

    @patch("src.api.routes.content.generate_content")
    def test_create_content_validation_word_count_too_low(self, mock_generate, client):
        """Test content creation validates word count."""
        invalid_request = {
            "topic": "Valid topic for testing",
            "word_count": 50,  # Below minimum
        }
        response = client.post("/api/v1/content/generate", json=invalid_request)
        assert response.status_code == 422

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

        # Verify content was added to storage
        content_id = data["content_id"]
        assert content_id in content_storage
        assert content_storage[content_id].status == ContentStatus.PENDING

    @patch("src.api.routes.content.generate_content")
    async def test_sync_content_generation_success(
        self, mock_generate, client, sample_content_request, sample_completed_content
    ):
        """Test synchronous content generation."""
        mock_generate.return_value = sample_completed_content

        response = client.post(
            "/api/v1/content/generate",
            json=sample_content_request,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["content"] is not None

    def test_list_content_pagination(self, client, sample_completed_content):
        """Test content listing with pagination."""
        # Add multiple content items
        for i in range(5):
            content = sample_completed_content.model_copy()
            content.id = f"test-{i}"
            content_storage[content.id] = content

        # Test limit
        response = client.get("/api/v1/content?limit=2")
        assert response.status_code == 200
        assert len(response.json()) == 2

        # Test offset
        response = client.get("/api/v1/content?limit=2&offset=3")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_content_success(self, client, sample_completed_content):
        """Test getting content by ID."""
        content_storage[sample_completed_content.id] = sample_completed_content

        response = client.get(f"/api/v1/content/{sample_completed_content.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_completed_content.id
        assert data["status"] == "completed"

    def test_get_content_status(self, client, sample_completed_content):
        """Test getting content status."""
        content_storage[sample_completed_content.id] = sample_completed_content

        response = client.get(f"/api/v1/content/{sample_completed_content.id}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["content_id"] == sample_completed_content.id
        assert data["status"] == "completed"
        assert "processing_time_seconds" in data

    def test_delete_content_success(self, client, sample_completed_content):
        """Test deleting content."""
        content_storage[sample_completed_content.id] = sample_completed_content

        response = client.delete(f"/api/v1/content/{sample_completed_content.id}")
        assert response.status_code == 200
        assert sample_completed_content.id not in content_storage


class TestExportEndpoints:
    """Test content export endpoints."""

    def test_export_nonexistent_content(self, client):
        """Test exporting non-existent content returns 404."""
        response = client.get("/api/v1/content/nonexistent-id/export")
        assert response.status_code == 404

    def test_export_incomplete_content(self, client, sample_completed_content):
        """Test exporting incomplete content returns 400."""
        # Set status to pending
        pending_content = sample_completed_content.model_copy()
        pending_content.status = ContentStatus.PENDING
        content_storage[pending_content.id] = pending_content

        response = client.get(f"/api/v1/content/{pending_content.id}/export")
        assert response.status_code == 400
        assert "not ready" in response.json()["detail"].lower()

    def test_export_markdown(self, client, sample_completed_content):
        """Test exporting content as Markdown."""
        content_storage[sample_completed_content.id] = sample_completed_content

        response = client.get(
            f"/api/v1/content/{sample_completed_content.id}/export?format=markdown"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/markdown"
        assert "attachment" in response.headers["content-disposition"]
        assert ".md" in response.headers["content-disposition"]

        content = response.content.decode("utf-8")
        assert "---" in content  # YAML frontmatter
        assert "Test Content" in content

    def test_export_html(self, client, sample_completed_content):
        """Test exporting content as HTML."""
        content_storage[sample_completed_content.id] = sample_completed_content

        response = client.get(f"/api/v1/content/{sample_completed_content.id}/export?format=html")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html"
        assert ".html" in response.headers["content-disposition"]

        content = response.content.decode("utf-8")
        assert "<!DOCTYPE html>" in content
        assert "<title>" in content

    def test_export_json(self, client, sample_completed_content):
        """Test exporting content as JSON."""
        content_storage[sample_completed_content.id] = sample_completed_content

        response = client.get(f"/api/v1/content/{sample_completed_content.id}/export?format=json")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        import json

        data = json.loads(response.content)
        assert data["id"] == sample_completed_content.id
        assert data["content"] is not None

    def test_export_txt(self, client, sample_completed_content):
        """Test exporting content as plain text."""
        content_storage[sample_completed_content.id] = sample_completed_content

        response = client.get(f"/api/v1/content/{sample_completed_content.id}/export?format=txt")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain"

    def test_get_export_formats(self, client):
        """Test getting available export formats."""
        response = client.get("/api/v1/content/test-id/export/formats")
        assert response.status_code == 200

        data = response.json()
        assert "formats" in data
        assert len(data["formats"]) == 5

        format_ids = [f["id"] for f in data["formats"]]
        assert "markdown" in format_ids
        assert "html" in format_ids
        assert "json" in format_ids


class TestContentModels:
    """Test content model validation."""

    def test_content_request_defaults(self):
        """Test ContentRequest has sensible defaults."""
        request = ContentRequest(topic="Test topic here")
        assert request.content_type == ContentType.BLOG_POST
        assert request.tone == "professional"
        assert request.language == "en"
        assert request.word_count == 1500

    def test_content_request_validation_topic_min_length(self):
        """Test ContentRequest validates minimum topic length."""
        with pytest.raises(ValueError):
            ContentRequest(topic="hi")  # Too short

    def test_content_request_validation_word_count_min(self):
        """Test ContentRequest validates minimum word count."""
        with pytest.raises(ValueError):
            ContentRequest(topic="Valid topic", word_count=50)  # Too few words

    def test_content_request_validation_word_count_max(self):
        """Test ContentRequest validates maximum word count."""
        with pytest.raises(ValueError):
            ContentRequest(topic="Valid topic", word_count=15000)  # Too many words

    def test_content_request_with_keywords(self):
        """Test ContentRequest with keywords."""
        request = ContentRequest(
            topic="AI in content marketing",
            keywords=["AI", "marketing", "content"],
        )
        assert len(request.keywords) == 3
        assert "AI" in request.keywords

    def test_content_response_status_enum(self):
        """Test ContentStatus enum values."""
        assert ContentStatus.PENDING.value == "pending"
        assert ContentStatus.RESEARCHING.value == "researching"
        assert ContentStatus.COMPLETED.value == "completed"
        assert ContentStatus.FAILED.value == "failed"


class TestAPIErrorHandling:
    """Test API error handling."""

    @patch("src.api.routes.content.generate_content")
    def test_generation_error_handling(self, mock_generate, client, sample_content_request):
        """Test that generation errors are handled properly."""
        mock_generate.side_effect = Exception("LLM API Error")

        response = client.post(
            "/api/v1/content/generate",
            json=sample_content_request,
        )
        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()

    def test_invalid_content_type(self, client):
        """Test invalid content type returns validation error."""
        invalid_request = {
            "topic": "Valid topic for testing",
            "content_type": "invalid_type",
        }
        response = client.post("/api/v1/content/generate", json=invalid_request)
        assert response.status_code == 422

    def test_invalid_export_format(self, client, sample_completed_content):
        """Test invalid export format returns error."""
        content_storage[sample_completed_content.id] = sample_completed_content

        response = client.get(
            f"/api/v1/content/{sample_completed_content.id}/export?format=invalid"
        )
        assert response.status_code == 422
