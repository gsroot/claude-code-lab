"""SQLAlchemy ORM models for Content Mate."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.models.content import ContentStatus, ContentType


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class ContentDB(Base):
    """Content database model."""

    __tablename__ = "content"

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Request fields
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(
        String(50),
        default=ContentType.BLOG_POST.value,
        nullable=False,
    )
    target_audience: Mapped[str | None] = mapped_column(Text, nullable=True)
    tone: Mapped[str] = mapped_column(String(50), default="professional")
    language: Mapped[str] = mapped_column(String(10), default="en")
    word_count: Mapped[int] = mapped_column(Integer, default=1500)
    keywords: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    additional_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=ContentStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Generated content
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    outline: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    research: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    seo: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    images: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    processing_time_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    # User relationship (optional, for future multi-user support)
    user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    user: Mapped["UserDB | None"] = relationship("UserDB", back_populates="contents")

    # Indexes
    __table_args__ = (
        Index("idx_content_created_at", created_at.desc()),
        Index("idx_content_user_id", user_id),
    )

    def __repr__(self) -> str:
        return f"<Content(id={self.id}, topic={self.topic[:30]}..., status={self.status})>"


class UserDB(Base):
    """User database model."""

    __tablename__ = "users"

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # User info
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    contents: Mapped[list["ContentDB"]] = relationship(
        "ContentDB",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
