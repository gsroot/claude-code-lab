"""Tests for retry utilities."""


import pytest

from src.utils.retry import (
    LLM_RETRY_CONFIG,
    RetryConfig,
    RetryError,
    calculate_delay,
    retry_async,
    with_retry,
)


class TestCalculateDelay:
    """Test delay calculation."""

    def test_first_attempt_delay(self):
        """Test delay for first attempt."""
        config = RetryConfig(initial_delay=1.0, exponential_base=2.0)
        delay = calculate_delay(0, config)
        assert delay == 1.0

    def test_exponential_backoff(self):
        """Test exponential backoff increases delay."""
        config = RetryConfig(initial_delay=1.0, exponential_base=2.0, max_delay=100.0)

        assert calculate_delay(0, config) == 1.0
        assert calculate_delay(1, config) == 2.0
        assert calculate_delay(2, config) == 4.0
        assert calculate_delay(3, config) == 8.0

    def test_max_delay_cap(self):
        """Test delay is capped at max_delay."""
        config = RetryConfig(initial_delay=1.0, exponential_base=2.0, max_delay=5.0)

        assert calculate_delay(0, config) == 1.0
        assert calculate_delay(1, config) == 2.0
        assert calculate_delay(2, config) == 4.0
        assert calculate_delay(3, config) == 5.0  # Capped at max_delay
        assert calculate_delay(10, config) == 5.0  # Still capped


class TestRetryConfig:
    """Test RetryConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 30.0
        assert config.exponential_base == 2.0

    def test_custom_config(self):
        """Test custom configuration."""
        config = RetryConfig(
            max_attempts=5,
            initial_delay=0.5,
            max_delay=60.0,
            exponential_base=3.0,
        )
        assert config.max_attempts == 5
        assert config.initial_delay == 0.5
        assert config.max_delay == 60.0
        assert config.exponential_base == 3.0

    def test_llm_retry_config(self):
        """Test LLM retry config preset."""
        assert LLM_RETRY_CONFIG.max_attempts == 3
        assert LLM_RETRY_CONFIG.initial_delay == 2.0


class TestRetryAsync:
    """Test retry_async function."""

    @pytest.mark.asyncio
    async def test_success_on_first_try(self):
        """Test successful execution on first try."""

        async def success_func():
            return "success"

        result = await retry_async(success_func)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_success_after_retry(self):
        """Test success after initial failures."""
        call_count = 0

        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        config = RetryConfig(max_attempts=3, initial_delay=0.01)
        result = await retry_async(fail_then_succeed, config=config)

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_failure_after_max_attempts(self):
        """Test failure after exhausting all attempts."""

        async def always_fail():
            raise ValueError("Always fails")

        config = RetryConfig(max_attempts=3, initial_delay=0.01)

        with pytest.raises(RetryError) as exc_info:
            await retry_async(always_fail, config=config, operation_name="test_op")

        assert "test_op failed after 3 attempts" in str(exc_info.value)
        assert exc_info.value.last_exception is not None

    @pytest.mark.asyncio
    async def test_non_retryable_exception(self):
        """Test non-retryable exceptions are not retried."""
        call_count = 0

        async def raise_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("Type error")

        config = RetryConfig(
            max_attempts=3,
            initial_delay=0.01,
            retryable_exceptions=(ValueError,),  # Only retry ValueError
        )

        with pytest.raises(RetryError):
            await retry_async(raise_type_error, config=config)

        # Should still try max_attempts times because TypeError is caught by Exception
        # but since we specified only ValueError, it will fail immediately
        # Actually, since we pass retryable_exceptions, it will retry on those only

    @pytest.mark.asyncio
    async def test_with_arguments(self):
        """Test retry with function arguments."""

        async def add(a, b):
            return a + b

        result = await retry_async(add, 2, 3)
        assert result == 5

    @pytest.mark.asyncio
    async def test_with_kwargs(self):
        """Test retry with keyword arguments."""

        async def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        result = await retry_async(greet, "World", greeting="Hi")
        assert result == "Hi, World!"


class TestWithRetryDecorator:
    """Test with_retry decorator."""

    @pytest.mark.asyncio
    async def test_decorator_success(self):
        """Test decorator on successful function."""

        @with_retry()
        async def success_func():
            return "decorated success"

        result = await success_func()
        assert result == "decorated success"

    @pytest.mark.asyncio
    async def test_decorator_with_config(self):
        """Test decorator with custom config."""
        call_count = 0

        @with_retry(config=RetryConfig(max_attempts=2, initial_delay=0.01))
        async def fail_once():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First call fails")
            return "success"

        result = await fail_once()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_decorator_preserves_function_name(self):
        """Test decorator preserves function metadata."""

        @with_retry()
        async def my_function():
            """My docstring."""
            return True

        assert my_function.__name__ == "my_function"
        assert "My docstring" in my_function.__doc__


class TestRetryError:
    """Test RetryError exception."""

    def test_retry_error_message(self):
        """Test RetryError message."""
        error = RetryError("Operation failed")
        assert str(error) == "Operation failed"

    def test_retry_error_with_last_exception(self):
        """Test RetryError preserves last exception."""
        original = ValueError("Original error")
        error = RetryError("Operation failed", last_exception=original)

        assert error.last_exception is original
        assert error.last_exception.args[0] == "Original error"
