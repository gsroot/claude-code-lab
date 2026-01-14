"""Logging configuration for Content Mate."""

import sys
from pathlib import Path
from typing import Any

from loguru import logger

from src.utils.config import settings


def setup_logging(
    log_level: str = "INFO",
    log_file: str | None = None,
    json_format: bool = False,
) -> None:
    """Configure logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for log output
        json_format: Whether to use JSON format for logs
    """
    # Remove default handler
    logger.remove()

    # Console format
    if json_format:
        console_format = "{message}"
    else:
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

    # Add console handler
    logger.add(
        sys.stderr,
        format=console_format,
        level=log_level,
        colorize=not json_format,
        serialize=json_format,
    )

    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level=log_level,
            rotation="10 MB",
            retention="7 days",
            compression="gz",
        )

    logger.info(f"Logging configured: level={log_level}, json={json_format}")


def get_pipeline_logger(content_id: str) -> Any:
    """Get a logger with content_id context.

    Args:
        content_id: Unique content generation ID

    Returns:
        Logger bound with content_id context
    """
    return logger.bind(content_id=content_id)


class PipelineLogger:
    """Structured logger for pipeline operations."""

    def __init__(self, content_id: str, topic: str | None = None):
        """Initialize pipeline logger.

        Args:
            content_id: Unique content generation ID
            topic: Content topic for context
        """
        self.content_id = content_id
        self.topic = topic
        self._logger = logger.bind(content_id=content_id)

    def _format_message(self, phase: str, message: str) -> str:
        """Format log message with context."""
        return f"[{self.content_id[:8]}][{phase}] {message}"

    def phase_start(self, phase: str) -> None:
        """Log phase start."""
        self._logger.info(self._format_message(phase, f"Starting {phase} phase"))

    def phase_complete(self, phase: str, duration_ms: float | None = None) -> None:
        """Log phase completion."""
        msg = f"Completed {phase} phase"
        if duration_ms:
            msg += f" ({duration_ms:.0f}ms)"
        self._logger.info(self._format_message(phase, msg))

    def phase_error(self, phase: str, error: Exception) -> None:
        """Log phase error."""
        self._logger.error(self._format_message(phase, f"Failed: {error}"))

    def phase_retry(self, phase: str, attempt: int, max_attempts: int, delay: float) -> None:
        """Log retry attempt."""
        self._logger.warning(
            self._format_message(phase, f"Retry {attempt}/{max_attempts} after {delay:.1f}s")
        )

    def info(self, phase: str, message: str) -> None:
        """Log info message."""
        self._logger.info(self._format_message(phase, message))

    def warning(self, phase: str, message: str) -> None:
        """Log warning message."""
        self._logger.warning(self._format_message(phase, message))

    def error(self, phase: str, message: str) -> None:
        """Log error message."""
        self._logger.error(self._format_message(phase, message))

    def debug(self, phase: str, message: str) -> None:
        """Log debug message."""
        self._logger.debug(self._format_message(phase, message))


# Initialize logging on module import
if settings.is_development:
    setup_logging(log_level="DEBUG")
else:
    setup_logging(log_level="INFO", json_format=True)
