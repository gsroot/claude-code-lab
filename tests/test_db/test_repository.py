"""Tests for content repository."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.db.models import ContentDB
from src.db.repository import ContentRepository
from src.models.content import (
    ContentOutline,
    ContentRequest,
    ContentResponse,
    ContentStatus,
    ContentType,
)


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def content_repo(mock_session):
    """Create content repository with mock session."""
    return ContentRepository(mock_session)


@pytest.fixture
def sample_request():
    """Sample content request."""
    return ContentRequest(
        topic="Test topic for content generation",
        content_type=ContentType.BLOG_POST,
        tone="professional",
        language="en",
        word_count=1500,
        keywords=["test", "content"],
    )


@pytest.fixture
def sample_content_db():
    """Sample content database record."""
    return ContentDB(
        id="test-id-123",
        topic="Test topic for content generation",
        content_type="blog_post",
        tone="professional",
        language="en",
        word_count=1500,
        keywords=["test", "content"],
        status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


class TestContentRepository:
    """Tests for ContentRepository."""

    @pytest.mark.asyncio
    async def test_create_content(self, content_repo, sample_request, mock_session):
        """Test creating a new content record."""
        # Act
        await content_repo.create(sample_request)

        # Assert
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()

        # Verify the created content has expected attributes
        created_content = mock_session.add.call_args[0][0]
        assert created_content.topic == sample_request.topic
        assert created_content.content_type == sample_request.content_type.value
        assert created_content.tone == sample_request.tone
        assert created_content.status == ContentStatus.PENDING.value

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, content_repo, sample_content_db, mock_session):
        """Test getting content by ID when found."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_content_db
        mock_session.execute.return_value = mock_result

        # Act
        result = await content_repo.get_by_id("test-id-123")

        # Assert
        assert result == sample_content_db
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, content_repo, mock_session):
        """Test getting content by ID when not found."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        result = await content_repo.get_by_id("nonexistent-id")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all(self, content_repo, sample_content_db, mock_session):
        """Test getting all content records."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_content_db]
        mock_session.execute.return_value = mock_result

        # Act
        result = await content_repo.get_all(limit=10, offset=0)

        # Assert
        assert len(result) == 1
        assert result[0] == sample_content_db

    @pytest.mark.asyncio
    async def test_update_status(self, content_repo, mock_session):
        """Test updating content status."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        # Act
        result = await content_repo.update_status(
            "test-id-123",
            ContentStatus.COMPLETED,
        )

        # Assert
        assert result is True
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_status_not_found(self, content_repo, mock_session):
        """Test updating status for non-existent content."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        # Act
        result = await content_repo.update_status(
            "nonexistent-id",
            ContentStatus.COMPLETED,
        )

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_update_content(self, content_repo, mock_session):
        """Test updating content with generated results."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        outline = ContentOutline(
            title="Test Title",
            hook="Test hook",
            sections=[{"header": "Section 1", "purpose": "Test", "points": ["Point 1"]}],
            conclusion_points=["Conclusion"],
        )

        # Act
        result = await content_repo.update_content(
            "test-id-123",
            content="Generated content here",
            outline=outline,
            status=ContentStatus.COMPLETED,
            processing_time=5.5,
        )

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_content(self, content_repo, mock_session):
        """Test deleting content."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        # Act
        result = await content_repo.delete("test-id-123")

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_content_not_found(self, content_repo, mock_session):
        """Test deleting non-existent content."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        # Act
        result = await content_repo.delete("nonexistent-id")

        # Assert
        assert result is False

    def test_to_response(self, sample_content_db):
        """Test converting database model to response model."""
        # Add additional fields
        sample_content_db.content = "Generated content"
        sample_content_db.outline = {
            "title": "Test Title",
            "hook": "Test hook",
            "sections": [],
            "conclusion_points": [],
        }
        sample_content_db.research = {
            "sources": [],
            "key_facts": ["Fact 1"],
            "statistics": [],
            "quotes": [],
            "competitor_insights": [],
        }
        sample_content_db.completed_at = datetime.utcnow()
        sample_content_db.processing_time_seconds = 5.5

        # Act
        response = ContentRepository.to_response(sample_content_db)

        # Assert
        assert isinstance(response, ContentResponse)
        assert response.id == sample_content_db.id
        assert response.content == "Generated content"
        assert response.outline.title == "Test Title"
        assert len(response.research.key_facts) == 1


class TestContentRepositoryCount:
    """Tests for content count functionality."""

    @pytest.mark.asyncio
    async def test_count_all(self, content_repo, mock_session):
        """Test counting all content."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_session.execute.return_value = mock_result

        # Act
        result = await content_repo.count()

        # Assert
        assert result == 5

    @pytest.mark.asyncio
    async def test_count_by_status(self, content_repo, mock_session):
        """Test counting content by status."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar.return_value = 3
        mock_session.execute.return_value = mock_result

        # Act
        result = await content_repo.count(status=ContentStatus.COMPLETED)

        # Assert
        assert result == 3

    @pytest.mark.asyncio
    async def test_count_empty(self, content_repo, mock_session):
        """Test counting when no content exists."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        result = await content_repo.count()

        # Assert
        assert result == 0
