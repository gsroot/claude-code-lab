"""Tests for the Planner agent."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.planner import PlannerAgent
from src.models.content import ContentOutline, ContentRequest, ContentType, ResearchResult


@pytest.fixture
def planner():
    """Create a planner agent instance."""
    with patch("src.agents.base.ChatAnthropic"):
        return PlannerAgent()


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
        keywords=["AI", "content marketing", "automation"],
    )


@pytest.fixture
def sample_research():
    """Create sample research results."""
    return ResearchResult(
        key_facts=[
            "AI can increase content production by 10x",
            "80% of marketers plan to use AI tools by 2025",
            "Content quality improves with AI assistance",
        ],
        statistics=[
            "Market size: $6.14 billion in 2025",
            "Growth rate: 29.57% CAGR",
        ],
        quotes=[
            "AI is revolutionizing how we create content - Industry Expert",
        ],
        competitor_insights=[
            "Jasper AI focuses on marketing copy",
            "Copy.ai targets small businesses",
        ],
    )


class TestPlannerAgent:
    """Test cases for PlannerAgent."""

    def test_agent_initialization(self, planner):
        """Test agent initializes correctly."""
        assert planner.name == "planner"
        assert "outline" in planner.description.lower() or "plan" in planner.description.lower()

    def test_system_prompt_contains_guidelines(self, planner):
        """Test system prompt contains necessary guidelines."""
        prompt = planner.system_prompt.lower()
        assert "structure" in prompt or "outline" in prompt
        assert "json" in prompt

    @pytest.mark.asyncio
    async def test_process_requires_request(self, planner):
        """Test that process raises error without request."""
        with pytest.raises(ValueError, match="No content request"):
            await planner.process({})

    def test_build_planning_prompt(self, planner, sample_request, sample_research):
        """Test planning prompt construction."""
        prompt = planner._build_planning_prompt(sample_request, sample_research)

        # Check that key elements are in the prompt
        assert sample_request.topic in prompt
        assert "blog_post" in prompt
        assert "1500" in prompt
        assert "professional" in prompt
        assert "AI" in prompt  # keyword
        assert "Marketing professionals" in prompt  # target audience

        # Check research is included
        assert "AI can increase content production" in prompt
        assert "$6.14 billion" in prompt

    def test_build_planning_prompt_without_research(self, planner, sample_request):
        """Test planning prompt works without research."""
        prompt = planner._build_planning_prompt(sample_request, None)

        assert sample_request.topic in prompt
        assert "RESEARCH FINDINGS" not in prompt


class TestOutlineParsing:
    """Test content outline parsing."""

    @pytest.fixture
    def planner(self):
        with patch("src.agents.base.ChatAnthropic"):
            return PlannerAgent()

    def test_parse_valid_json(self, planner):
        """Test parsing valid JSON response."""
        json_response = json.dumps(
            {
                "title": "How AI is Transforming Content Marketing",
                "hook": "In 2025, AI is no longer optional for marketers.",
                "sections": [
                    {
                        "header": "The Rise of AI in Marketing",
                        "purpose": "Set context",
                        "points": ["Point 1", "Point 2"],
                    },
                    {
                        "header": "Key Benefits",
                        "purpose": "Show value",
                        "points": ["Speed", "Quality", "Scale"],
                    },
                ],
                "conclusion_points": ["AI is essential", "Start now"],
                "cta": "Try AI tools today",
            }
        )

        result = planner._parse_outline(json_response)

        assert isinstance(result, ContentOutline)
        assert result.title == "How AI is Transforming Content Marketing"
        assert "2025" in result.hook
        assert len(result.sections) == 2
        assert result.sections[0]["header"] == "The Rise of AI in Marketing"
        assert len(result.conclusion_points) == 2
        assert result.cta == "Try AI tools today"

    def test_parse_json_with_surrounding_text(self, planner):
        """Test parsing JSON embedded in text."""
        response = """Here's the outline:

{
    "title": "Test Title",
    "hook": "Test hook",
    "sections": [{"header": "Section 1", "purpose": "Test", "points": ["A", "B"]}],
    "conclusion_points": ["Summary"],
    "cta": "Act now"
}

Hope this helps!"""

        result = planner._parse_outline(response)

        assert result.title == "Test Title"
        assert result.hook == "Test hook"

    def test_parse_invalid_json_fallback(self, planner):
        """Test fallback parsing when JSON is invalid."""
        response = """
Title: My Great Article

## Introduction
- Point one
- Point two

## Main Content
- Key insight 1
- Key insight 2
- Key insight 3

## Conclusion
- Wrap up
"""
        result = planner._parse_outline(response)

        # Should return a valid ContentOutline even with fallback
        assert isinstance(result, ContentOutline)
        assert result.title is not None
        assert len(result.sections) > 0

    def test_parse_empty_response(self, planner):
        """Test parsing empty response uses fallback."""
        result = planner._parse_outline("")

        # Should return default structure
        assert isinstance(result, ContentOutline)
        assert len(result.sections) > 0

    def test_parse_malformed_json(self, planner):
        """Test parsing malformed JSON uses fallback."""
        response = '{"title": "Test", "sections": [incomplete'

        result = planner._parse_outline(response)

        # Should not crash, return valid outline
        assert isinstance(result, ContentOutline)


class TestPlannerIntegration:
    """Integration-style tests for PlannerAgent."""

    @pytest.fixture
    def planner(self):
        with patch("src.agents.base.ChatAnthropic"):
            return PlannerAgent()

    @pytest.mark.asyncio
    async def test_process_with_mocked_llm(self, planner, sample_request, sample_research):
        """Test full process with mocked LLM response."""
        mock_response = MagicMock()
        mock_response.content = json.dumps(
            {
                "title": "AI Content Marketing Guide",
                "hook": "Transform your marketing with AI.",
                "sections": [
                    {
                        "header": "Introduction",
                        "purpose": "Set stage",
                        "points": ["Why AI matters"],
                    },
                    {
                        "header": "Implementation",
                        "purpose": "How to",
                        "points": ["Step 1", "Step 2"],
                    },
                ],
                "conclusion_points": ["AI is the future"],
                "cta": "Start using AI today",
            }
        )

        planner.invoke = AsyncMock(return_value=mock_response)

        state = {
            "request": sample_request,
            "research": sample_research,
            "messages": [],
        }

        result = await planner.process(state)

        assert "outline" in result
        assert result["outline"].title == "AI Content Marketing Guide"
        assert result["status"] == "planning_complete"
        assert len(result["messages"]) > 0
