"""Retry utilities with exponential backoff for robust error handling."""

import asyncio
import functools
from typing import Any, Callable, TypeVar
from collections.abc import Awaitable

from loguru import logger

T = TypeVar("T")


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, message: str, last_exception: Exception | None = None):
        super().__init__(message)
        self.last_exception = last_exception


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    ):
        """Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            exponential_base: Base for exponential backoff
            retryable_exceptions: Tuple of exception types to retry on
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions


# Default configurations for different scenarios
DEFAULT_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=30.0,
)

LLM_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay=2.0,
    max_delay=60.0,
    exponential_base=2.0,
)

NETWORK_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    initial_delay=0.5,
    max_delay=30.0,
    exponential_base=2.0,
)


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay for a given attempt using exponential backoff.

    Args:
        attempt: Current attempt number (0-indexed)
        config: Retry configuration

    Returns:
        Delay in seconds
    """
    delay = config.initial_delay * (config.exponential_base ** attempt)
    return min(delay, config.max_delay)


async def retry_async(
    func: Callable[..., Awaitable[T]],
    *args: Any,
    config: RetryConfig | None = None,
    operation_name: str = "operation",
    **kwargs: Any,
) -> T:
    """Execute an async function with retry logic.

    Args:
        func: Async function to execute
        *args: Positional arguments for the function
        config: Retry configuration
        operation_name: Name of operation for logging
        **kwargs: Keyword arguments for the function

    Returns:
        Result from the function

    Raises:
        RetryError: When all attempts are exhausted
    """
    config = config or DEFAULT_RETRY_CONFIG
    last_exception: Exception | None = None

    for attempt in range(config.max_attempts):
        try:
            return await func(*args, **kwargs)

        except config.retryable_exceptions as e:
            last_exception = e
            remaining = config.max_attempts - attempt - 1

            if remaining > 0:
                delay = calculate_delay(attempt, config)
                logger.warning(
                    f"[Retry] {operation_name} failed (attempt {attempt + 1}/{config.max_attempts}): {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"[Retry] {operation_name} failed after {config.max_attempts} attempts: {e}"
                )

    raise RetryError(
        f"{operation_name} failed after {config.max_attempts} attempts",
        last_exception=last_exception,
    )


def with_retry(
    config: RetryConfig | None = None,
    operation_name: str | None = None,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator to add retry logic to async functions.

    Args:
        config: Retry configuration
        operation_name: Name of operation for logging

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            name = operation_name or func.__name__
            return await retry_async(func, *args, config=config, operation_name=name, **kwargs)
        return wrapper
    return decorator
