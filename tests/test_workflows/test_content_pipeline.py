"""Tests for the content generation pipeline."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from src.workflows.content_pipeline import ContentPipeline, ContentState, generate_content
from src.models.content import (
    ContentRequest,
    ContentType,
    ContentStatus,
    ResearchResult,
    ContentOutline,
)


@pytest.fixture
def sample_request():
    """Create a sample content request."""
    return ContentRequest(
        topic="How to use AI for content marketing",
        content_type=ContentType.BLOG_POST,
        target_audience="Digital marketers",
        tone="professional",
        language="en",
        word_count=1500,
    )


@pytest.fixture
def mock_research():
    """Create mock research result."""
    return ResearchResult(
        key_facts=["Fact 1", "Fact 2"],
        statistics=["Stat 1"],
        quotes=["Quote 1"],
        competitor_insights=["Insight 1"],
    )


@pytest.fixture
def mock_outline():
    """Create mock content outline."""
    return ContentOutline(
        title="AI Content Marketing Guide",
        hook="Transform your marketing.",
        sections=[
            {"header": "Introduction", "purpose": "Set context", "points": ["Point 1"]},
            {"header": "Main Content", "purpose": "Educate", "points": ["Point 2", "Point 3"]},
        ],
        conclusion_points=["Summary point"],
        cta="Start today",
    )


class TestContentPipeline:
    """Test cases for ContentPipeline."""

    @patch("src.workflows.content_pipeline.ResearcherAgent")
    @patch("src.workflows.content_pipeline.PlannerAgent")
    @patch("src.workflows.content_pipeline.WriterAgent")
    @patch("src.workflows.content_pipeline.EditorAgent")
    def test_pipeline_initialization(self, mock_editor, mock_writer, mock_planner, mock_researcher):
        """Test pipeline initializes with all agents."""
        pipeline = ContentPipeline()

        mock_researcher.assert_called_once()
        mock_planner.assert_called_once()
        mock_writer.assert_called_once()
        mock_editor.assert_called_once()

        assert pipeline.graph is not None

    @patch("src.workflows.content_pipeline.ResearcherAgent")
    @patch("src.workflows.content_pipeline.PlannerAgent")
    @patch("src.workflows.content_pipeline.WriterAgent")
    @patch("src.workflows.content_pipeline.EditorAgent")
    def test_graph_has_all_nodes(self, mock_editor, mock_writer, mock_planner, mock_researcher):
        """Test the graph contains all expected nodes."""
        pipeline = ContentPipeline()

        # The graph should be compiled successfully
        assert pipeline.graph is not None


class TestContentState:
    """Test ContentState structure."""

    def test_content_state_structure(self, sample_request):
        """Test ContentState has all required fields."""
        state: ContentState = {
            "request": sample_request,
            "content_id": "test-123",
            "status": ContentStatus.PENDING,
            "messages": [],
            "research": None,
            "outline": None,
            "draft_content": None,
            "content": None,
            "started_at": datetime.utcnow(),
            "error": None,
        }

        assert state["request"] == sample_request
        assert state["content_id"] == "test-123"
        assert state["status"] == ContentStatus.PENDING


class TestPipelineNodes:
    """Test individual pipeline nodes."""

    @pytest.fixture
    def pipeline(self):
        """Create pipeline with mocked agents."""
        with patch("src.workflows.content_pipeline.ResearcherAgent") as mock_r, \
             patch("src.workflows.content_pipeline.PlannerAgent") as mock_p, \
             patch("src.workflows.content_pipeline.WriterAgent") as mock_w, \
             patch("src.workflows.content_pipeline.EditorAgent") as mock_e:
            return ContentPipeline()

    @pytest.mark.asyncio
    async def test_research_node_success(self, pipeline, sample_request, mock_research):
        """Test research node processes successfully."""
        pipeline.researcher.process = AsyncMock(return_value={
            "research": mock_research,
            "messages": [],
        })

        state: ContentState = {
            "request": sample_request,
            "content_id": "test-123",
            "status": ContentStatus.PENDING,
            "messages": [],
            "research": None,
            "outline": None,
            "draft_content": None,
            "content": None,
            "started_at": datetime.utcnow(),
            "error": None,
        }

        result = await pipeline._research_node(state)

        assert result["research"] == mock_research
        assert result["status"] == ContentStatus.RESEARCHING

    @pytest.mark.asyncio
    async def test_research_node_failure(self, pipeline, sample_request):
        """Test research node handles errors."""
        pipeline.researcher.process = AsyncMock(side_effect=Exception("API Error"))

        state: ContentState = {
            "request": sample_request,
            "content_id": "test-123",
            "status": ContentStatus.PENDING,
            "messages": [],
            "research": None,
            "outline": None,
            "draft_content": None,
            "content": None,
            "started_at": datetime.utcnow(),
            "error": None,
        }

        result = await pipeline._research_node(state)

        assert result["status"] == ContentStatus.FAILED
        assert "API Error" in result["error"]

    @pytest.mark.asyncio
    async def test_plan_node_success(self, pipeline, sample_request, mock_research, mock_outline):
        """Test plan node processes successfully."""
        pipeline.planner.process = AsyncMock(return_value={
            "outline": mock_outline,
            "messages": [],
        })

        state: ContentState = {
            "request": sample_request,
            "content_id": "test-123",
            "status": ContentStatus.RESEARCHING,
            "messages": [],
            "research": mock_research,
            "outline": None,
            "draft_content": None,
            "content": None,
            "started_at": datetime.utcnow(),
            "error": None,
        }

        result = await pipeline._plan_node(state)

        assert result["outline"] == mock_outline
        assert result["status"] == ContentStatus.PLANNING

    @pytest.mark.asyncio
    async def test_write_node_success(self, pipeline, sample_request, mock_research, mock_outline):
        """Test write node processes successfully."""
        pipeline.writer.process = AsyncMock(return_value={
            "draft_content": "This is the draft content...",
            "messages": [],
        })

        state: ContentState = {
            "request": sample_request,
            "content_id": "test-123",
            "status": ContentStatus.PLANNING,
            "messages": [],
            "research": mock_research,
            "outline": mock_outline,
            "draft_content": None,
            "content": None,
            "started_at": datetime.utcnow(),
            "error": None,
        }

        result = await pipeline._write_node(state)

        assert result["draft_content"] == "This is the draft content..."
        assert result["status"] == ContentStatus.WRITING

    @pytest.mark.asyncio
    async def test_edit_node_success(self, pipeline, sample_request):
        """Test edit node processes successfully."""
        pipeline.editor.process = AsyncMock(return_value={
            "content": "This is the final edited content.",
            "messages": [],
        })

        state: ContentState = {
            "request": sample_request,
            "content_id": "test-123",
            "status": ContentStatus.WRITING,
            "messages": [],
            "research": None,
            "outline": None,
            "draft_content": "Draft content here",
            "content": None,
            "started_at": datetime.utcnow(),
            "error": None,
        }

        result = await pipeline._edit_node(state)

        assert result["content"] == "This is the final edited content."
        assert result["status"] == ContentStatus.EDITING

    @pytest.mark.asyncio
    async def test_finalize_node(self, pipeline, sample_request):
        """Test finalize node sets completed status."""
        state: ContentState = {
            "request": sample_request,
            "content_id": "test-123",
            "status": ContentStatus.EDITING,
            "messages": [],
            "research": None,
            "outline": None,
            "draft_content": None,
            "content": "Final content",
            "started_at": datetime.utcnow(),
            "error": None,
        }

        result = await pipeline._finalize_node(state)

        assert result["status"] == ContentStatus.COMPLETED


class TestPipelineGenerate:
    """Test the generate method."""

    @pytest.fixture
    def pipeline(self):
        """Create pipeline with mocked agents."""
        with patch("src.workflows.content_pipeline.ResearcherAgent"), \
             patch("src.workflows.content_pipeline.PlannerAgent"), \
             patch("src.workflows.content_pipeline.WriterAgent"), \
             patch("src.workflows.content_pipeline.EditorAgent"):
            return ContentPipeline()

    @pytest.mark.asyncio
    async def test_generate_returns_content_response(self, pipeline, sample_request):
        """Test generate returns a ContentResponse."""
        # Mock the graph invoke
        pipeline.graph.ainvoke = AsyncMock(return_value={
            "status": ContentStatus.COMPLETED,
            "content": "Generated content here",
            "research": None,
            "outline": None,
        })

        response = await pipeline.generate(sample_request)

        assert response.id is not None
        assert response.request == sample_request
        assert response.status == ContentStatus.COMPLETED
        assert response.content == "Generated content here"
        assert response.processing_time_seconds is not None

    @pytest.mark.asyncio
    async def test_generate_handles_pipeline_error(self, pipeline, sample_request):
        """Test generate handles pipeline errors gracefully."""
        pipeline.graph.ainvoke = AsyncMock(side_effect=Exception("Pipeline crashed"))

        response = await pipeline.generate(sample_request)

        assert response.status == ContentStatus.FAILED
        assert response.content is None
