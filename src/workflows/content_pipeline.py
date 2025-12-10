"""Main content generation pipeline using LangGraph."""

import uuid
from datetime import datetime
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from loguru import logger

from src.agents import EditorAgent, ResearcherAgent, WriterAgent
from src.models.content import (
    ContentRequest,
    ContentResponse,
    ContentStatus,
    ResearchResult,
    ContentOutline,
)


class ContentState(TypedDict):
    """State object passed through the content generation pipeline."""

    # Input
    request: ContentRequest
    content_id: str

    # Processing state
    status: ContentStatus
    messages: Annotated[list[BaseMessage], add_messages]

    # Agent outputs
    research: ResearchResult | None
    outline: ContentOutline | None
    draft_content: str | None
    content: str | None

    # Metadata
    started_at: datetime
    error: str | None


class ContentPipeline:
    """LangGraph-based content generation pipeline.

    Orchestrates multiple agents to create high-quality content:
    1. Researcher: Gathers information and facts
    2. Planner: Creates content outline (optional)
    3. Writer: Writes the initial draft
    4. Editor: Polishes and improves the content
    """

    def __init__(self):
        """Initialize the content pipeline with all agents."""
        self.researcher = ResearcherAgent()
        self.writer = WriterAgent()
        self.editor = EditorAgent()

        self.graph = self._build_graph()
        logger.info("ContentPipeline initialized")

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow.

        Returns:
            Compiled StateGraph
        """
        # Create the graph
        workflow = StateGraph(ContentState)

        # Add nodes for each agent
        workflow.add_node("research", self._research_node)
        workflow.add_node("write", self._write_node)
        workflow.add_node("edit", self._edit_node)
        workflow.add_node("finalize", self._finalize_node)

        # Define the edges (flow)
        workflow.set_entry_point("research")

        workflow.add_edge("research", "write")
        workflow.add_edge("write", "edit")
        workflow.add_edge("edit", "finalize")
        workflow.add_edge("finalize", END)

        # Compile the graph
        return workflow.compile()

    async def _research_node(self, state: ContentState) -> dict[str, Any]:
        """Execute the research agent.

        Args:
            state: Current pipeline state

        Returns:
            Updated state with research results
        """
        logger.info(f"[{state['content_id']}] Starting research phase")
        try:
            result = await self.researcher.process(dict(state))
            return {
                "research": result.get("research"),
                "status": ContentStatus.RESEARCHING,
                "messages": result.get("messages", []),
            }
        except Exception as e:
            logger.error(f"Research failed: {e}")
            return {"error": str(e), "status": ContentStatus.FAILED}

    async def _write_node(self, state: ContentState) -> dict[str, Any]:
        """Execute the writer agent.

        Args:
            state: Current pipeline state

        Returns:
            Updated state with draft content
        """
        logger.info(f"[{state['content_id']}] Starting writing phase")
        try:
            result = await self.writer.process(dict(state))
            return {
                "draft_content": result.get("draft_content"),
                "status": ContentStatus.WRITING,
                "messages": result.get("messages", []),
            }
        except Exception as e:
            logger.error(f"Writing failed: {e}")
            return {"error": str(e), "status": ContentStatus.FAILED}

    async def _edit_node(self, state: ContentState) -> dict[str, Any]:
        """Execute the editor agent.

        Args:
            state: Current pipeline state

        Returns:
            Updated state with edited content
        """
        logger.info(f"[{state['content_id']}] Starting editing phase")
        try:
            result = await self.editor.process(dict(state))
            return {
                "content": result.get("content"),
                "status": ContentStatus.EDITING,
                "messages": result.get("messages", []),
            }
        except Exception as e:
            logger.error(f"Editing failed: {e}")
            return {"error": str(e), "status": ContentStatus.FAILED}

    async def _finalize_node(self, state: ContentState) -> dict[str, Any]:
        """Finalize the content generation.

        Args:
            state: Current pipeline state

        Returns:
            Final state update
        """
        logger.info(f"[{state['content_id']}] Finalizing content")
        return {"status": ContentStatus.COMPLETED}

    async def generate(self, request: ContentRequest) -> ContentResponse:
        """Generate content using the full pipeline.

        Args:
            request: Content generation request

        Returns:
            Generated content response
        """
        content_id = str(uuid.uuid4())
        started_at = datetime.utcnow()

        logger.info(f"Starting content generation [{content_id}]: {request.topic}")

        # Initialize state
        initial_state: ContentState = {
            "request": request,
            "content_id": content_id,
            "status": ContentStatus.PENDING,
            "messages": [],
            "research": None,
            "outline": None,
            "draft_content": None,
            "content": None,
            "started_at": started_at,
            "error": None,
        }

        # Run the pipeline
        try:
            final_state = await self.graph.ainvoke(initial_state)
            completed_at = datetime.utcnow()
            processing_time = (completed_at - started_at).total_seconds()

            logger.info(
                f"Content generation completed [{content_id}] "
                f"in {processing_time:.2f}s"
            )

            return ContentResponse(
                id=content_id,
                status=final_state.get("status", ContentStatus.COMPLETED),
                request=request,
                research=final_state.get("research"),
                outline=final_state.get("outline"),
                content=final_state.get("content"),
                created_at=started_at,
                completed_at=completed_at,
                processing_time_seconds=processing_time,
            )

        except Exception as e:
            logger.error(f"Pipeline failed [{content_id}]: {e}")
            return ContentResponse(
                id=content_id,
                status=ContentStatus.FAILED,
                request=request,
                created_at=started_at,
            )


# Singleton instance
pipeline = ContentPipeline()


async def generate_content(request: ContentRequest) -> ContentResponse:
    """Convenience function to generate content.

    Args:
        request: Content generation request

    Returns:
        Generated content response
    """
    return await pipeline.generate(request)
