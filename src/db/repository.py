"""Repository pattern for database operations."""

from datetime import datetime
from typing import Any, cast
from uuid import uuid4

from loguru import logger
from sqlalchemy import delete, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import ContentDB
from src.models.content import (
    ContentOutline,
    ContentRequest,
    ContentResponse,
    ContentStatus,
    ResearchResult,
    SEOMetadata,
)


class ContentRepository:
    """Repository for content database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, request: ContentRequest) -> ContentDB:
        """Create a new content record.

        Args:
            request: Content generation request

        Returns:
            Created content record
        """
        content = ContentDB(
            id=str(uuid4()),
            topic=request.topic,
            content_type=request.content_type.value,
            target_audience=request.target_audience,
            tone=request.tone,
            language=request.language,
            word_count=request.word_count,
            keywords=request.keywords if request.keywords else None,
            additional_instructions=request.additional_instructions,
            status=ContentStatus.PENDING.value,
        )

        self.session.add(content)
        await self.session.flush()
        await self.session.refresh(content)

        logger.info(f"Created content record: {content.id}")
        return content

    async def get_by_id(self, content_id: str) -> ContentDB | None:
        """Get content by ID.

        Args:
            content_id: Content ID

        Returns:
            Content record or None
        """
        result = await self.session.execute(select(ContentDB).where(ContentDB.id == content_id))
        return result.scalar_one_or_none()

    async def get_all(
        self,
        limit: int = 10,
        offset: int = 0,
        status: ContentStatus | None = None,
        user_id: str | None = None,
    ) -> list[ContentDB]:
        """Get all content records with pagination.

        Args:
            limit: Maximum number of records
            offset: Number of records to skip
            status: Filter by status
            user_id: Filter by user ID

        Returns:
            List of content records
        """
        query = select(ContentDB).order_by(ContentDB.created_at.desc())

        if status:
            query = query.where(ContentDB.status == status.value)
        if user_id:
            query = query.where(ContentDB.user_id == user_id)

        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_status(
        self,
        content_id: str,
        status: ContentStatus,
        error_message: str | None = None,
    ) -> bool:
        """Update content status.

        Args:
            content_id: Content ID
            status: New status
            error_message: Optional error message for failed status

        Returns:
            True if updated, False if not found
        """
        values: dict[str, Any] = {"status": status.value}
        if error_message:
            values["error_message"] = error_message

        result = await self.session.execute(
            update(ContentDB).where(ContentDB.id == content_id).values(**values)
        )

        rowcount = cast(CursorResult[Any], result).rowcount or 0
        return rowcount > 0

    async def update_content(
        self,
        content_id: str,
        content: str | None = None,
        outline: ContentOutline | None = None,
        research: ResearchResult | None = None,
        seo: SEOMetadata | None = None,
        status: ContentStatus | None = None,
        processing_time: float | None = None,
    ) -> bool:
        """Update content with generated results.

        Args:
            content_id: Content ID
            content: Generated content text
            outline: Content outline
            research: Research results
            seo: SEO metadata
            status: New status
            processing_time: Processing time in seconds

        Returns:
            True if updated, False if not found
        """
        values: dict[str, Any] = {"updated_at": datetime.utcnow()}

        if content is not None:
            values["content"] = content
        if outline is not None:
            values["outline"] = outline.model_dump()
        if research is not None:
            values["research"] = research.model_dump()
        if seo is not None:
            values["seo"] = seo.model_dump()
        if status is not None:
            values["status"] = status.value
            if status == ContentStatus.COMPLETED:
                values["completed_at"] = datetime.utcnow()
        if processing_time is not None:
            values["processing_time_seconds"] = processing_time

        result = await self.session.execute(
            update(ContentDB).where(ContentDB.id == content_id).values(**values)
        )

        rowcount = cast(CursorResult[Any], result).rowcount or 0
        return rowcount > 0

    async def delete(self, content_id: str) -> bool:
        """Delete content by ID.

        Args:
            content_id: Content ID

        Returns:
            True if deleted, False if not found
        """
        result = await self.session.execute(delete(ContentDB).where(ContentDB.id == content_id))

        rowcount = cast(CursorResult[Any], result).rowcount or 0
        return rowcount > 0

    async def count(
        self,
        status: ContentStatus | None = None,
        user_id: str | None = None,
    ) -> int:
        """Count content records.

        Args:
            status: Filter by status
            user_id: Filter by user ID

        Returns:
            Number of records
        """
        from sqlalchemy import func

        query = select(func.count(ContentDB.id))

        if status:
            query = query.where(ContentDB.status == status.value)
        if user_id:
            query = query.where(ContentDB.user_id == user_id)

        result = await self.session.execute(query)
        return result.scalar() or 0

    @staticmethod
    def to_response(content: ContentDB) -> ContentResponse:
        """Convert database model to response model.

        Args:
            content: Database content record

        Returns:
            Content response model
        """
        from src.models.content import ContentType

        return ContentResponse(
            id=content.id,
            status=ContentStatus(content.status),
            request=ContentRequest(
                topic=content.topic,
                content_type=ContentType(content.content_type),
                target_audience=content.target_audience,
                tone=content.tone,
                language=content.language,
                word_count=content.word_count,
                keywords=content.keywords or [],
                additional_instructions=content.additional_instructions,
            ),
            content=content.content,
            outline=ContentOutline(**content.outline) if content.outline else None,
            research=ResearchResult(**content.research) if content.research else None,
            seo=SEOMetadata(**content.seo) if content.seo else None,
            images=content.images or [],
            created_at=content.created_at,
            completed_at=content.completed_at,
            processing_time_seconds=content.processing_time_seconds,
        )
