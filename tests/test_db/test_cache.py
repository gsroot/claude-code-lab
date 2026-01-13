"""Tests for Redis cache module."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.db.cache import ContentCache, RateLimiter


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock()
    redis.set = AsyncMock()
    redis.delete = AsyncMock()
    redis.incr = AsyncMock()
    redis.scan_iter = MagicMock()
    return redis


@pytest.fixture
def content_cache(mock_redis):
    """Create content cache with mock Redis."""
    return ContentCache(mock_redis)


@pytest.fixture
def rate_limiter(mock_redis):
    """Create rate limiter with mock Redis."""
    return RateLimiter(mock_redis)


class TestContentCache:
    """Tests for ContentCache."""

    @pytest.mark.asyncio
    async def test_get_content_found(self, content_cache, mock_redis):
        """Test getting cached content when found."""
        # Setup
        content_data = {"id": "test-123", "content": "Test content"}
        mock_redis.get.return_value = json.dumps(content_data)

        # Act
        result = await content_cache.get_content("test-123")

        # Assert
        assert result == content_data
        mock_redis.get.assert_called_once_with("content:test-123")

    @pytest.mark.asyncio
    async def test_get_content_not_found(self, content_cache, mock_redis):
        """Test getting cached content when not found."""
        # Setup
        mock_redis.get.return_value = None

        # Act
        result = await content_cache.get_content("nonexistent-123")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_set_content(self, content_cache, mock_redis):
        """Test caching content data."""
        # Setup
        content_data = {"id": "test-123", "content": "Test content"}

        # Act
        await content_cache.set_content("test-123", content_data)

        # Assert
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == "content:test-123"
        assert json.loads(call_args[0][1])["id"] == "test-123"

    @pytest.mark.asyncio
    async def test_set_content_with_custom_ttl(self, content_cache, mock_redis):
        """Test caching content with custom TTL."""
        # Setup
        content_data = {"id": "test-123", "content": "Test content"}

        # Act
        await content_cache.set_content("test-123", content_data, ttl=7200)

        # Assert
        mock_redis.set.assert_called_once()
        call_kwargs = mock_redis.set.call_args[1]
        assert call_kwargs["ex"] == 7200

    @pytest.mark.asyncio
    async def test_delete_content(self, content_cache, mock_redis):
        """Test deleting cached content."""
        # Act
        await content_cache.delete_content("test-123")

        # Assert
        mock_redis.delete.assert_called_once_with("content:test-123")

    @pytest.mark.asyncio
    async def test_get_status(self, content_cache, mock_redis):
        """Test getting cached status."""
        # Setup
        mock_redis.get.return_value = "completed"

        # Act
        result = await content_cache.get_status("test-123")

        # Assert
        assert result == "completed"
        mock_redis.get.assert_called_once_with("status:test-123")

    @pytest.mark.asyncio
    async def test_set_status(self, content_cache, mock_redis):
        """Test caching status."""
        # Act
        await content_cache.set_status("test-123", "processing")

        # Assert
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == "status:test-123"
        assert call_args[0][1] == "processing"

    @pytest.mark.asyncio
    async def test_get_progress(self, content_cache, mock_redis):
        """Test getting progress data."""
        # Setup
        progress_data = {"phase": "writing", "progress": 50, "message": "Writing..."}
        mock_redis.get.return_value = json.dumps(progress_data)

        # Act
        result = await content_cache.get_progress("test-123")

        # Assert
        assert result == progress_data
        mock_redis.get.assert_called_once_with("progress:test-123")

    @pytest.mark.asyncio
    async def test_set_progress(self, content_cache, mock_redis):
        """Test updating progress."""
        # Act
        await content_cache.set_progress("test-123", "writing", 50.0, "Writing...")

        # Assert
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == "progress:test-123"
        data = json.loads(call_args[0][1])
        assert data["phase"] == "writing"
        assert data["progress"] == 50.0

    @pytest.mark.asyncio
    async def test_delete_progress(self, content_cache, mock_redis):
        """Test deleting progress data."""
        # Act
        await content_cache.delete_progress("test-123")

        # Assert
        mock_redis.delete.assert_called_once_with("progress:test-123")


class TestRateLimiter:
    """Tests for RateLimiter."""

    @pytest.mark.asyncio
    async def test_is_allowed_first_request(self, rate_limiter, mock_redis):
        """Test first request is allowed."""
        # Setup
        mock_redis.get.return_value = None

        # Act
        is_allowed, remaining = await rate_limiter.is_allowed(
            "user-123",
            max_requests=10,
            window_seconds=60,
        )

        # Assert
        assert is_allowed is True
        assert remaining == 9
        mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_allowed_under_limit(self, rate_limiter, mock_redis):
        """Test request under limit is allowed."""
        # Setup
        mock_redis.get.return_value = "5"

        # Act
        is_allowed, remaining = await rate_limiter.is_allowed(
            "user-123",
            max_requests=10,
            window_seconds=60,
        )

        # Assert
        assert is_allowed is True
        assert remaining == 4
        mock_redis.incr.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_allowed_at_limit(self, rate_limiter, mock_redis):
        """Test request at limit is not allowed."""
        # Setup
        mock_redis.get.return_value = "10"

        # Act
        is_allowed, remaining = await rate_limiter.is_allowed(
            "user-123",
            max_requests=10,
            window_seconds=60,
        )

        # Assert
        assert is_allowed is False
        assert remaining == 0
        mock_redis.incr.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_remaining_no_requests(self, rate_limiter, mock_redis):
        """Test getting remaining when no requests made."""
        # Setup
        mock_redis.get.return_value = None

        # Act
        remaining = await rate_limiter.get_remaining("user-123", max_requests=10)

        # Assert
        assert remaining == 10

    @pytest.mark.asyncio
    async def test_get_remaining_some_requests(self, rate_limiter, mock_redis):
        """Test getting remaining after some requests."""
        # Setup
        mock_redis.get.return_value = "3"

        # Act
        remaining = await rate_limiter.get_remaining("user-123", max_requests=10)

        # Assert
        assert remaining == 7

    @pytest.mark.asyncio
    async def test_reset(self, rate_limiter, mock_redis):
        """Test resetting rate limit."""
        # Act
        await rate_limiter.reset("user-123")

        # Assert
        mock_redis.delete.assert_called_once_with("ratelimit:user-123")
