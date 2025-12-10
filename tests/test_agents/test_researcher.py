"""Tests for the Researcher agent."""

import pytest
from unittest.mock import AsyncMock, patch

from src.agents.researcher import ResearcherAgent
from src.models.content import ContentRequest, ContentType


@pytest.fixture
def researcher():
    """Create a researcher agent instance."""
    with patch("src.agents.base.ChatAnthropic"):
        return ResearcherAgent()


@pytest.fixture
def sample_request():
    """Create a sample content request."""
    return ContentRequest(
        topic="The impact of AI on content marketing",
        content_type=ContentType.BLOG_POST,
        target_audience="Marketing professionals",
        tone="professional",
        language="en",
        word_count=1500,
    )


class TestResearcherAgent:
    """Test cases for ResearcherAgent."""

    def test_agent_initialization(self, researcher):
        """Test agent initializes correctly."""
        assert researcher.name == "researcher"
        assert "research" in researcher.description.lower()

    def test_system_prompt_contains_guidelines(self, researcher):
        """Test system prompt contains necessary guidelines."""
        prompt = researcher.system_prompt.lower()
        assert "research" in prompt
        assert "facts" in prompt or "information" in prompt

    @pytest.mark.asyncio
    async def test_process_requires_request(self, researcher):
        """Test that process raises error without request."""
        with pytest.raises(ValueError, match="No content request"):
            await researcher.process({})

    def test_parse_research_extracts_facts(self, researcher):
        """Test research parsing extracts facts."""
        sample_response = """
Key Facts:
- AI is transforming content creation
- 80% of marketers use AI tools
- Content quality has improved

Statistics:
- Market size: $6.14 billion
- Growth rate: 29.57% CAGR
"""
        result = researcher._parse_research(sample_response)

        assert len(result.key_facts) > 0
        assert len(result.statistics) > 0


class TestResearchParsing:
    """Test research result parsing."""

    @pytest.fixture
    def researcher(self):
        with patch("src.agents.base.ChatAnthropic"):
            return ResearcherAgent()

    def test_empty_response(self, researcher):
        """Test parsing empty response."""
        result = researcher._parse_research("")
        assert result.key_facts == []
        assert result.statistics == []

    def test_malformed_response(self, researcher):
        """Test parsing malformed response."""
        result = researcher._parse_research("Random text without structure")
        # Should not crash, just return empty results
        assert isinstance(result.key_facts, list)
        assert isinstance(result.statistics, list)
