"""Custom exceptions for ContentForge AI."""

from typing import Any


class ContentForgeError(Exception):
    """Base exception for ContentForge AI."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class AgentError(ContentForgeError):
    """Exception raised when an agent fails to process."""

    def __init__(
        self,
        message: str,
        agent_name: str,
        phase: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, details)
        self.agent_name = agent_name
        self.phase = phase

    def __str__(self) -> str:
        base = f"[{self.agent_name}] {self.message}"
        if self.phase:
            base = f"[{self.agent_name}:{self.phase}] {self.message}"
        return base


class ResearchError(AgentError):
    """Exception raised during research phase."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, agent_name="Researcher", phase="research", details=details)


class PlanningError(AgentError):
    """Exception raised during planning phase."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, agent_name="Planner", phase="planning", details=details)


class WritingError(AgentError):
    """Exception raised during writing phase."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, agent_name="Writer", phase="writing", details=details)


class EditingError(AgentError):
    """Exception raised during editing phase."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, agent_name="Editor", phase="editing", details=details)


class PipelineError(ContentForgeError):
    """Exception raised when the pipeline fails."""

    def __init__(
        self,
        message: str,
        content_id: str | None = None,
        failed_phase: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, details)
        self.content_id = content_id
        self.failed_phase = failed_phase


class LLMError(ContentForgeError):
    """Exception raised when LLM API fails."""

    def __init__(
        self,
        message: str,
        model: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, details)
        self.model = model
        self.status_code = status_code


class RateLimitError(LLMError):
    """Exception raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: float | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, status_code=429, details=details)
        self.retry_after = retry_after


class ValidationError(ContentForgeError):
    """Exception raised when validation fails."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, details)
        self.field = field


class MCPError(ContentForgeError):
    """Exception raised when MCP server fails."""

    def __init__(
        self,
        message: str,
        server_name: str | None = None,
        tool_name: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, details)
        self.server_name = server_name
        self.tool_name = tool_name
