"""Main content generation pipeline using LangGraph with retry and error handling."""

import time
import uuid
from datetime import datetime
from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from loguru import logger

from src.agents import EditorAgent, PlannerAgent, ResearcherAgent, WriterAgent
from src.models.content import (
    ContentOutline,
    ContentRequest,
    ContentResponse,
    ContentStatus,
    ResearchResult,
)
from src.utils.exceptions import (
    ContentMateError,
    EditingError,
    PlanningError,
    ResearchError,
    WritingError,
)
from src.utils.logging import PipelineLogger
from src.utils.retry import LLM_RETRY_CONFIG, RetryError, retry_async


class ContentState(TypedDict):
    """State object passed through the content generation pipeline."""

    # Input
    request: ContentRequest
    content_id: str

    # Processing state
    status: ContentStatus
    messages: Annotated[list[BaseMessage], add_messages]
    current_phase: str

    # Agent outputs
    research: ResearchResult | None
    outline: ContentOutline | None
    draft_content: str | None
    content: str | None

    # Metadata
    started_at: datetime
    error: str | None
    retry_count: int
    phase_timings: dict[str, float]


class ContentPipeline:
    """LangGraph-based content generation pipeline with retry and error handling.

    Orchestrates multiple agents to create high-quality content:
    1. Researcher: Gathers information and facts
    2. Planner: Creates content outline
    3. Writer: Writes the initial draft
    4. Editor: Polishes and improves the content

    Features:
    - Automatic retry with exponential backoff
    - Detailed error tracking
    - Phase timing metrics
    - Structured logging
    """

    def __init__(self):
        """Initialize the content pipeline with all agents."""
        self.researcher = ResearcherAgent()
        self.planner = PlannerAgent()
        self.writer = WriterAgent()
        self.editor = EditorAgent()

        self.graph = self._build_graph()
        logger.info("ContentPipeline initialized with 4 agents (retry enabled)")

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow.

        Pipeline: Research → Plan → Write → Edit → Finalize

        Returns:
            Compiled StateGraph
        """
        workflow = StateGraph(ContentState)

        # Add nodes for each agent
        workflow.add_node("research", self._research_node)
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("write", self._write_node)
        workflow.add_node("edit", self._edit_node)
        workflow.add_node("finalize", self._finalize_node)

        # Define the edges (flow): Research → Plan → Write → Edit → Finalize
        workflow.set_entry_point("research")

        workflow.add_edge("research", "plan")
        workflow.add_edge("plan", "write")
        workflow.add_edge("write", "edit")
        workflow.add_edge("edit", "finalize")
        workflow.add_edge("finalize", END)

        return workflow.compile()

    async def _execute_with_retry(
        self,
        agent_process: Any,
        state: ContentState,
        phase_name: str,
        error_class: type[ContentMateError],
    ) -> dict[str, Any]:
        """Execute an agent with retry logic.

        Args:
            agent_process: Agent's process method
            state: Current pipeline state
            phase_name: Name of the current phase
            error_class: Exception class to raise on failure

        Returns:
            Agent result dictionary
        """
        pipeline_logger = PipelineLogger(state["content_id"])
        start_time = time.time()

        pipeline_logger.phase_start(phase_name)

        try:
            result = await retry_async(
                agent_process,
                dict(state),
                config=LLM_RETRY_CONFIG,
                operation_name=f"{phase_name}_agent",
            )

            elapsed_ms = (time.time() - start_time) * 1000
            pipeline_logger.phase_complete(phase_name, elapsed_ms)

            return result

        except RetryError as e:
            elapsed_ms = (time.time() - start_time) * 1000
            pipeline_logger.phase_error(phase_name, e)

            raise error_class(
                f"{phase_name} failed after retries: {e.last_exception}",
                details={
                    "content_id": state["content_id"],
                    "elapsed_ms": elapsed_ms,
                    "last_error": str(e.last_exception),
                },
            ) from e

    async def _research_node(self, state: ContentState) -> dict[str, Any]:
        """Execute the research agent with retry.

        Args:
            state: Current pipeline state

        Returns:
            Updated state with research results
        """
        try:
            result = await self._execute_with_retry(
                self.researcher.process,
                state,
                "research",
                ResearchError,
            )

            return {
                "research": result.get("research"),
                "status": ContentStatus.RESEARCHING,
                "current_phase": "research",
                "messages": result.get("messages", []),
            }

        except ResearchError as e:
            logger.error(f"[{state['content_id']}] Research failed: {e}")
            return {
                "error": str(e),
                "status": ContentStatus.FAILED,
                "current_phase": "research",
            }

    async def _plan_node(self, state: ContentState) -> dict[str, Any]:
        """Execute the planner agent with retry.

        Args:
            state: Current pipeline state

        Returns:
            Updated state with content outline
        """
        # Skip if previous phase failed
        if state.get("error"):
            return {"status": ContentStatus.FAILED}

        try:
            result = await self._execute_with_retry(
                self.planner.process,
                state,
                "planning",
                PlanningError,
            )

            return {
                "outline": result.get("outline"),
                "status": ContentStatus.PLANNING,
                "current_phase": "planning",
                "messages": result.get("messages", []),
            }

        except PlanningError as e:
            logger.error(f"[{state['content_id']}] Planning failed: {e}")
            return {
                "error": str(e),
                "status": ContentStatus.FAILED,
                "current_phase": "planning",
            }

    async def _write_node(self, state: ContentState) -> dict[str, Any]:
        """Execute the writer agent with retry.

        Args:
            state: Current pipeline state

        Returns:
            Updated state with draft content
        """
        # Skip if previous phase failed
        if state.get("error"):
            return {"status": ContentStatus.FAILED}

        try:
            result = await self._execute_with_retry(
                self.writer.process,
                state,
                "writing",
                WritingError,
            )

            return {
                "draft_content": result.get("draft_content"),
                "status": ContentStatus.WRITING,
                "current_phase": "writing",
                "messages": result.get("messages", []),
            }

        except WritingError as e:
            logger.error(f"[{state['content_id']}] Writing failed: {e}")
            return {
                "error": str(e),
                "status": ContentStatus.FAILED,
                "current_phase": "writing",
            }

    async def _edit_node(self, state: ContentState) -> dict[str, Any]:
        """Execute the editor agent with retry.

        Args:
            state: Current pipeline state

        Returns:
            Updated state with edited content
        """
        # Skip if previous phase failed
        if state.get("error"):
            return {"status": ContentStatus.FAILED}

        try:
            result = await self._execute_with_retry(
                self.editor.process,
                state,
                "editing",
                EditingError,
            )

            return {
                "content": result.get("content"),
                "status": ContentStatus.EDITING,
                "current_phase": "editing",
                "messages": result.get("messages", []),
            }

        except EditingError as e:
            logger.error(f"[{state['content_id']}] Editing failed: {e}")
            return {
                "error": str(e),
                "status": ContentStatus.FAILED,
                "current_phase": "editing",
            }

    async def _finalize_node(self, state: ContentState) -> dict[str, Any]:
        """Finalize the content generation.

        Args:
            state: Current pipeline state

        Returns:
            Final state update
        """
        content_id = state["content_id"]

        # Check if any error occurred
        if state.get("error"):
            logger.warning(f"[{content_id}] Pipeline completed with errors")
            return {
                "status": ContentStatus.FAILED,
                "current_phase": "finalize",
            }

        # Validate final content
        if not state.get("content"):
            logger.warning(f"[{content_id}] Pipeline completed but no content generated")
            return {
                "error": "No content was generated",
                "status": ContentStatus.FAILED,
                "current_phase": "finalize",
            }

        logger.info(f"[{content_id}] Content generation completed successfully")
        return {
            "status": ContentStatus.COMPLETED,
            "current_phase": "finalize",
        }

    async def generate(self, request: ContentRequest) -> ContentResponse:
        """Generate content using the full pipeline.

        Args:
            request: Content generation request

        Returns:
            Generated content response
        """
        content_id = str(uuid.uuid4())
        started_at = datetime.utcnow()

        logger.info(f"[{content_id}] Starting content generation: {request.topic[:50]}...")

        # Initialize state
        initial_state: ContentState = {
            "request": request,
            "content_id": content_id,
            "status": ContentStatus.PENDING,
            "messages": [],
            "current_phase": "init",
            "research": None,
            "outline": None,
            "draft_content": None,
            "content": None,
            "started_at": started_at,
            "error": None,
            "retry_count": 0,
            "phase_timings": {},
        }

        try:
            final_state = await self.graph.ainvoke(initial_state)
            completed_at = datetime.utcnow()
            processing_time = (completed_at - started_at).total_seconds()

            # Determine final status
            final_status = final_state.get("status", ContentStatus.COMPLETED)
            error_message = final_state.get("error")

            if final_status == ContentStatus.COMPLETED:
                logger.info(
                    f"[{content_id}] Generation completed successfully in {processing_time:.2f}s"
                )
            else:
                logger.warning(
                    f"[{content_id}] Generation failed at phase "
                    f"'{final_state.get('current_phase', 'unknown')}': {error_message}"
                )

            return ContentResponse(
                id=content_id,
                status=final_status,
                request=request,
                research=final_state.get("research"),
                outline=final_state.get("outline"),
                content=final_state.get("content"),
                created_at=started_at,
                completed_at=completed_at,
                processing_time_seconds=processing_time,
            )

        except Exception as e:
            completed_at = datetime.utcnow()
            processing_time = (completed_at - started_at).total_seconds()

            logger.error(f"[{content_id}] Pipeline crashed: {e}")

            return ContentResponse(
                id=content_id,
                status=ContentStatus.FAILED,
                request=request,
                created_at=started_at,
                completed_at=completed_at,
                processing_time_seconds=processing_time,
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
