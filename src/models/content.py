"""Content-related Pydantic models."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ContentType(str, Enum):
    """Supported content types."""

    BLOG_POST = "blog_post"
    ARTICLE = "article"
    SOCIAL_MEDIA = "social_media"
    EMAIL = "email"
    LANDING_PAGE = "landing_page"
    PRODUCT_DESCRIPTION = "product_description"


class ContentStatus(str, Enum):
    """Content generation status."""

    PENDING = "pending"
    RESEARCHING = "researching"
    PLANNING = "planning"
    WRITING = "writing"
    EDITING = "editing"
    OPTIMIZING = "optimizing"
    COMPLETED = "completed"
    FAILED = "failed"


class ContentRequest(BaseModel):
    """Request model for content generation."""

    topic: str = Field(..., min_length=5, max_length=500, description="Content topic or idea")
    content_type: ContentType = Field(default=ContentType.BLOG_POST)
    target_audience: str | None = Field(default=None, description="Target audience description")
    tone: str = Field(
        default="professional", description="Content tone (professional, casual, etc.)"
    )
    language: str = Field(default="en", description="Target language code")
    word_count: int = Field(default=1500, ge=100, le=10000, description="Target word count")
    keywords: list[str] = Field(default_factory=list, description="SEO keywords to include")
    additional_instructions: str | None = Field(default=None, description="Extra instructions")


class ResearchResult(BaseModel):
    """Research findings from the researcher agent."""

    sources: list[dict[str, Any]] = Field(default_factory=list)
    key_facts: list[str] = Field(default_factory=list)
    statistics: list[str] = Field(default_factory=list)
    quotes: list[str] = Field(default_factory=list)
    competitor_insights: list[str] = Field(default_factory=list)


class ContentOutline(BaseModel):
    """Content outline from the planner agent."""

    title: str
    hook: str = Field(description="Opening hook/introduction")
    sections: list[dict[str, Any]] = Field(description="Content sections with headers and points")
    conclusion_points: list[str] = Field(default_factory=list)
    cta: str | None = Field(default=None, description="Call to action")


class SEOMetadata(BaseModel):
    """SEO optimization data."""

    meta_title: str = Field(max_length=60)
    meta_description: str = Field(max_length=160)
    keywords: list[str] = Field(default_factory=list)
    slug: str
    readability_score: float = Field(ge=0, le=100)


class ContentResponse(BaseModel):
    """Final content generation response."""

    id: str
    status: ContentStatus
    request: ContentRequest
    research: ResearchResult | None = None
    outline: ContentOutline | None = None
    content: str | None = None
    seo: SEOMetadata | None = None
    images: list[str] = Field(default_factory=list, description="Generated image URLs")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    processing_time_seconds: float | None = None
