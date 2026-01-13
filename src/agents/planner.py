"""Content Planner Agent - Creates structured outlines based on research."""

import json
import re
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage

from src.agents.base import BaseAgent
from src.models.content import ContentOutline


class OutlineSection(TypedDict):
    """Section structure for outline parsing."""

    header: str
    purpose: str
    points: list[str]


class PlannerAgent(BaseAgent):
    """Agent responsible for creating content outlines and structure."""

    name = "planner"
    description = "Creates detailed content outlines based on research findings"

    system_prompt = """You are an expert content strategist and planner with years of experience structuring compelling content.

Your role is to:
1. Analyze research findings and identify the most compelling angles
2. Create a clear, logical structure for the content
3. Design an engaging opening hook that captures attention
4. Organize main points into well-structured sections
5. Plan a strong conclusion with clear takeaways

PLANNING PRINCIPLES:
1. Start with impact - Lead with the most interesting or valuable information
2. Logical flow - Each section should naturally lead to the next
3. Balance depth and breadth - Cover key points thoroughly without overwhelming
4. Reader-focused - Structure based on what the audience needs to know
5. Actionable - Include practical takeaways readers can apply

STRUCTURE GUIDELINES:
- Title: Compelling, clear, includes key benefit or hook
- Hook: 2-3 sentences that grab attention and establish relevance
- Sections: 3-5 main sections, each with a clear purpose
- Each section: Header + 3-5 key points to cover
- Conclusion: Summary + Call to action

OUTPUT FORMAT:
You must respond with a valid JSON object in this exact format:
{
    "title": "Your compelling title here",
    "hook": "Opening hook that grabs attention...",
    "sections": [
        {
            "header": "Section 1 Header",
            "purpose": "What this section accomplishes",
            "points": ["Point 1", "Point 2", "Point 3"]
        }
    ],
    "conclusion_points": ["Key takeaway 1", "Key takeaway 2"],
    "cta": "Clear call to action for the reader"
}"""

    async def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """Create a content outline based on research.

        Args:
            state: Current workflow state containing research results

        Returns:
            Updated state with content outline
        """
        request = state.get("request")
        research = state.get("research")

        if not request:
            raise ValueError("No content request found in state")

        # Build the planning prompt
        planning_prompt = self._build_planning_prompt(request, research)

        messages = [HumanMessage(content=planning_prompt)]
        response = await self.invoke(messages)

        # Parse the outline from response
        outline = self._parse_outline(response.content)

        return {
            **state,
            "outline": outline,
            "status": "planning_complete",
            "messages": state.get("messages", []) + [response],
        }

    def _build_planning_prompt(self, request: Any, research: Any) -> str:
        """Build the planning prompt from request and research.

        Args:
            request: Original content request
            research: Research results from researcher agent

        Returns:
            Formatted planning prompt
        """
        prompt_parts = [
            f"Create a detailed content outline for: {request.topic}",
            f"\nCONTENT TYPE: {request.content_type.value}",
            f"TARGET WORD COUNT: {request.word_count} words",
            f"TONE: {request.tone}",
            f"LANGUAGE: {request.language}",
        ]

        if request.target_audience:
            prompt_parts.append(f"TARGET AUDIENCE: {request.target_audience}")

        if request.keywords:
            prompt_parts.append(f"KEYWORDS TO INCORPORATE: {', '.join(request.keywords)}")

        if research:
            prompt_parts.append("\n--- RESEARCH FINDINGS ---")

            if research.key_facts:
                prompt_parts.append("\nKey Facts discovered:")
                for i, fact in enumerate(research.key_facts[:7], 1):
                    prompt_parts.append(f"  {i}. {fact}")

            if research.statistics:
                prompt_parts.append("\nRelevant Statistics:")
                for stat in research.statistics[:5]:
                    prompt_parts.append(f"  • {stat}")

            if research.quotes:
                prompt_parts.append("\nExpert Quotes available:")
                for quote in research.quotes[:3]:
                    prompt_parts.append(f'  "{quote}"')

            if research.competitor_insights:
                prompt_parts.append("\nCompetitor Insights:")
                for insight in research.competitor_insights[:3]:
                    prompt_parts.append(f"  • {insight}")

        if request.additional_instructions:
            prompt_parts.append(f"\nADDITIONAL REQUIREMENTS: {request.additional_instructions}")

        prompt_parts.append("\n--- INSTRUCTIONS ---")
        prompt_parts.append(
            "Based on the above information, create a comprehensive content outline."
        )
        prompt_parts.append("Respond ONLY with a valid JSON object in the specified format.")
        prompt_parts.append("Do not include any text before or after the JSON.")

        return "\n".join(prompt_parts)

    def _parse_outline(self, content: str) -> ContentOutline:
        """Parse LLM response into structured ContentOutline.

        Args:
            content: Raw LLM response content

        Returns:
            Structured ContentOutline
        """
        # Try to extract JSON from the response
        try:
            # First, try direct JSON parsing
            data = json.loads(content)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            json_match = re.search(r"\{[\s\S]*\}", content)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                except json.JSONDecodeError:
                    # Fallback to basic parsing
                    return self._fallback_parse(content)
            else:
                return self._fallback_parse(content)

        # Validate and construct ContentOutline
        try:
            return ContentOutline(
                title=data.get("title", "Untitled"),
                hook=data.get("hook", ""),
                sections=data.get("sections", []),
                conclusion_points=data.get("conclusion_points", []),
                cta=data.get("cta"),
            )
        except Exception:
            return self._fallback_parse(content)

    def _fallback_parse(self, content: str) -> ContentOutline:
        """Fallback parsing when JSON extraction fails.

        Args:
            content: Raw content to parse

        Returns:
            Basic ContentOutline with extracted information
        """
        lines = content.split("\n")
        title = "Content Outline"
        hook = ""
        sections: list[OutlineSection] = []
        current_section: OutlineSection | None = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try to extract title
            if line.lower().startswith("title:"):
                title = line[6:].strip().strip('"')
            elif "hook:" in line.lower():
                hook = line.split(":", 1)[1].strip().strip('"')
            elif line.startswith("#") or line.startswith("##"):
                # New section header
                header = line.lstrip("#").strip()
                if current_section:
                    sections.append(current_section)
                current_section = {"header": header, "purpose": "", "points": []}
            elif line.startswith("-") or line.startswith("•") or line.startswith("*"):
                point = line.lstrip("-•* ").strip()
                if current_section:
                    current_section["points"].append(point)

        if current_section:
            sections.append(current_section)

        # If no sections found, create a basic structure
        if not sections:
            sections = [
                {
                    "header": "Introduction",
                    "purpose": "Set the context",
                    "points": ["Introduce the topic", "Establish relevance"],
                },
                {
                    "header": "Main Content",
                    "purpose": "Core information",
                    "points": ["Key point 1", "Key point 2", "Key point 3"],
                },
                {
                    "header": "Conclusion",
                    "purpose": "Wrap up",
                    "points": ["Summary", "Call to action"],
                },
            ]

        return ContentOutline(
            title=title,
            hook=hook or "Engaging opening to capture reader attention.",
            sections=sections,
            conclusion_points=["Key takeaway from the content"],
            cta="Take the next step based on what you learned.",
        )
