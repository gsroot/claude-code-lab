"""Application configuration management."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # LLM API Keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/contentmate"
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    jwt_secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # MCP Servers
    mcp_fetch_server: str = "npx -y @anthropic/mcp-fetch"
    mcp_memory_server: str = "npx -y @anthropic/mcp-memory"

    # Content Generation
    default_llm_model: str = "claude-sonnet-4-20250514"
    max_tokens_per_request: int = 4096
    content_generation_timeout: int = 300

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
