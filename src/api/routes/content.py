"""Content generation API routes."""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import Response
from loguru import logger

from src.models.content import ContentRequest, ContentResponse, ContentStatus
from src.services.export_service import ExportFormat, ExportService
from src.workflows.content_pipeline import generate_content

router = APIRouter()

# In-memory storage for demo (use database in production)
content_storage: dict[str, ContentResponse] = {}


@router.post("/content/generate", response_model=ContentResponse)
async def create_content(request: ContentRequest):
    """Generate new content using the AI pipeline.

    This endpoint triggers the full content generation pipeline:
    1. Research - Gather information about the topic
    2. Write - Create the initial draft
    3. Edit - Polish and improve the content

    Args:
        request: Content generation request

    Returns:
        Generated content response
    """
    logger.info(f"Content generation request: {request.topic}")

    try:
        response = await generate_content(request)
        content_storage[response.id] = response
        return response
    except Exception as e:
        logger.error(f"Content generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/content/generate/async", response_model=dict)
async def create_content_async(
    request: ContentRequest,
    background_tasks: BackgroundTasks,
):
    """Start async content generation.

    Returns immediately with a content ID that can be used to check status.

    Args:
        request: Content generation request
        background_tasks: FastAPI background tasks

    Returns:
        Content ID for status checking
    """
    import uuid

    content_id = str(uuid.uuid4())

    # Create placeholder response
    placeholder = ContentResponse(
        id=content_id,
        status=ContentStatus.PENDING,
        request=request,
    )
    content_storage[content_id] = placeholder

    # Start background generation
    async def generate_in_background():
        try:
            response = await generate_content(request)
            # Update the ID to match our placeholder
            response.id = content_id
            content_storage[content_id] = response
        except Exception as e:
            logger.error(f"Background generation failed: {e}")
            content_storage[content_id].status = ContentStatus.FAILED

    background_tasks.add_task(generate_in_background)

    return {"content_id": content_id, "status": "processing"}


@router.get("/content/{content_id}", response_model=ContentResponse)
async def get_content(content_id: str):
    """Get content by ID.

    Args:
        content_id: Content ID

    Returns:
        Content response
    """
    if content_id not in content_storage:
        raise HTTPException(status_code=404, detail="Content not found")
    return content_storage[content_id]


@router.get("/content/{content_id}/status")
async def get_content_status(content_id: str):
    """Get content generation status.

    Args:
        content_id: Content ID

    Returns:
        Status information
    """
    if content_id not in content_storage:
        raise HTTPException(status_code=404, detail="Content not found")

    content = content_storage[content_id]
    return {
        "content_id": content_id,
        "status": content.status,
        "created_at": content.created_at,
        "completed_at": content.completed_at,
        "processing_time_seconds": content.processing_time_seconds,
    }


@router.get("/content", response_model=list[ContentResponse])
async def list_content(limit: int = 10, offset: int = 0):
    """List all generated content.

    Args:
        limit: Maximum number of results
        offset: Offset for pagination

    Returns:
        List of content responses
    """
    items = list(content_storage.values())
    items.sort(key=lambda x: x.created_at, reverse=True)
    return items[offset : offset + limit]


@router.delete("/content/{content_id}")
async def delete_content(content_id: str):
    """Delete content by ID.

    Args:
        content_id: Content ID

    Returns:
        Deletion confirmation
    """
    if content_id not in content_storage:
        raise HTTPException(status_code=404, detail="Content not found")

    del content_storage[content_id]
    return {"message": "Content deleted", "content_id": content_id}


@router.get("/content/{content_id}/export")
async def export_content(
    content_id: str,
    format: ExportFormat = Query(default=ExportFormat.MARKDOWN, description="Export format"),
):
    """Export content to various formats.

    Supported formats:
    - markdown: Markdown with YAML frontmatter
    - html: Styled HTML document
    - pdf: Print-ready HTML (save as PDF)
    - json: Complete JSON export with all metadata
    - txt: Plain text

    Args:
        content_id: Content ID
        format: Export format (markdown, html, pdf, json, txt)

    Returns:
        Exported content as file download
    """
    if content_id not in content_storage:
        raise HTTPException(status_code=404, detail="Content not found")

    content = content_storage[content_id]

    if content.status != ContentStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Content is not ready for export. Status: {content.status.value}",
        )

    try:
        exported = ExportService.export(content, format)
        filename = ExportService.get_filename(content, format)
        content_type = ExportService.get_content_type(format)

        return Response(
            content=exported,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/content/{content_id}/export/formats")
async def get_export_formats():
    """Get available export formats.

    Returns:
        List of available export formats with descriptions
    """
    return {
        "formats": [
            {
                "id": ExportFormat.MARKDOWN.value,
                "name": "Markdown",
                "extension": "md",
                "description": "Markdown format with YAML frontmatter",
            },
            {
                "id": ExportFormat.HTML.value,
                "name": "HTML",
                "extension": "html",
                "description": "Styled HTML document",
            },
            {
                "id": ExportFormat.PDF.value,
                "name": "PDF",
                "extension": "pdf",
                "description": "Print-ready document (save browser page as PDF)",
            },
            {
                "id": ExportFormat.JSON.value,
                "name": "JSON",
                "extension": "json",
                "description": "Complete JSON with all metadata and structure",
            },
            {
                "id": ExportFormat.TXT.value,
                "name": "Plain Text",
                "extension": "txt",
                "description": "Plain text without formatting",
            },
        ]
    }
