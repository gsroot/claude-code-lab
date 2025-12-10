"""Redis cache module for ContentForge AI."""

import json
from typing import Any

from loguru import logger
from redis.asyncio import Redis, from_url

from src.utils.config import settings

# Redis client instance
_redis_client: Redis | None = None


async def get_redis() -> Redis:
    """Get Redis client instance.

    Returns:
        Redis client
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    return _redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client

    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")


async def check_redis_connection() -> bool:
    """Check if Redis connection is healthy.

    Returns:
        True if connected, False otherwise
    """
    try:
        redis = await get_redis()
        await redis.ping()
        return True
    except Exception as e:
        logger.error(f"Redis connection check failed: {e}")
        return False


class ContentCache:
    """Cache manager for content data."""

    # Cache key prefixes
    CONTENT_PREFIX = "content:"
    STATUS_PREFIX = "status:"
    PROGRESS_PREFIX = "progress:"

    # Default TTL (time to live) in seconds
    DEFAULT_TTL = 3600  # 1 hour
    PROGRESS_TTL = 300  # 5 minutes for progress data

    def __init__(self, redis: Redis):
        self.redis = redis

    @classmethod
    async def create(cls) -> "ContentCache":
        """Create a ContentCache instance.

        Returns:
            ContentCache instance
        """
        redis = await get_redis()
        return cls(redis)

    # Content caching methods
    async def get_content(self, content_id: str) -> dict[str, Any] | None:
        """Get cached content by ID.

        Args:
            content_id: Content ID

        Returns:
            Cached content data or None
        """
        key = f"{self.CONTENT_PREFIX}{content_id}"
        data = await self.redis.get(key)

        if data:
            return json.loads(data)
        return None

    async def set_content(
        self,
        content_id: str,
        content_data: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """Cache content data.

        Args:
            content_id: Content ID
            content_data: Content data to cache
            ttl: Time to live in seconds
        """
        key = f"{self.CONTENT_PREFIX}{content_id}"
        await self.redis.set(
            key,
            json.dumps(content_data, default=str),
            ex=ttl or self.DEFAULT_TTL,
        )

    async def delete_content(self, content_id: str) -> None:
        """Delete cached content.

        Args:
            content_id: Content ID
        """
        key = f"{self.CONTENT_PREFIX}{content_id}"
        await self.redis.delete(key)

    # Status caching methods
    async def get_status(self, content_id: str) -> str | None:
        """Get cached content status.

        Args:
            content_id: Content ID

        Returns:
            Status string or None
        """
        key = f"{self.STATUS_PREFIX}{content_id}"
        return await self.redis.get(key)

    async def set_status(self, content_id: str, status: str, ttl: int | None = None) -> None:
        """Cache content status.

        Args:
            content_id: Content ID
            status: Status string
            ttl: Time to live in seconds
        """
        key = f"{self.STATUS_PREFIX}{content_id}"
        await self.redis.set(key, status, ex=ttl or self.DEFAULT_TTL)

    # Progress tracking methods
    async def get_progress(self, content_id: str) -> dict[str, Any] | None:
        """Get generation progress data.

        Args:
            content_id: Content ID

        Returns:
            Progress data or None
        """
        key = f"{self.PROGRESS_PREFIX}{content_id}"
        data = await self.redis.get(key)

        if data:
            return json.loads(data)
        return None

    async def set_progress(
        self,
        content_id: str,
        phase: str,
        progress: float,
        message: str | None = None,
    ) -> None:
        """Update generation progress.

        Args:
            content_id: Content ID
            phase: Current phase
            progress: Progress percentage (0-100)
            message: Optional progress message
        """
        key = f"{self.PROGRESS_PREFIX}{content_id}"
        data = {
            "phase": phase,
            "progress": progress,
            "message": message,
        }
        await self.redis.set(
            key,
            json.dumps(data),
            ex=self.PROGRESS_TTL,
        )

    async def delete_progress(self, content_id: str) -> None:
        """Delete progress data.

        Args:
            content_id: Content ID
        """
        key = f"{self.PROGRESS_PREFIX}{content_id}"
        await self.redis.delete(key)

    # Utility methods
    async def clear_all_content_cache(self) -> int:
        """Clear all content cache.

        Returns:
            Number of keys deleted
        """
        pattern = f"{self.CONTENT_PREFIX}*"
        keys = []

        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            return await self.redis.delete(*keys)
        return 0


class RateLimiter:
    """Rate limiter using Redis."""

    RATE_LIMIT_PREFIX = "ratelimit:"

    def __init__(self, redis: Redis):
        self.redis = redis

    @classmethod
    async def create(cls) -> "RateLimiter":
        """Create a RateLimiter instance.

        Returns:
            RateLimiter instance
        """
        redis = await get_redis()
        return cls(redis)

    async def is_allowed(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, int]:
        """Check if request is allowed under rate limit.

        Args:
            identifier: Unique identifier (e.g., user ID, IP address)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        key = f"{self.RATE_LIMIT_PREFIX}{identifier}"

        # Get current count
        current = await self.redis.get(key)

        if current is None:
            # First request in window
            await self.redis.set(key, 1, ex=window_seconds)
            return True, max_requests - 1

        current_count = int(current)

        if current_count >= max_requests:
            return False, 0

        # Increment count
        await self.redis.incr(key)
        return True, max_requests - current_count - 1

    async def get_remaining(
        self,
        identifier: str,
        max_requests: int,
    ) -> int:
        """Get remaining requests for identifier.

        Args:
            identifier: Unique identifier
            max_requests: Maximum requests allowed

        Returns:
            Remaining requests
        """
        key = f"{self.RATE_LIMIT_PREFIX}{identifier}"
        current = await self.redis.get(key)

        if current is None:
            return max_requests

        return max(0, max_requests - int(current))

    async def reset(self, identifier: str) -> None:
        """Reset rate limit for identifier.

        Args:
            identifier: Unique identifier
        """
        key = f"{self.RATE_LIMIT_PREFIX}{identifier}"
        await self.redis.delete(key)
