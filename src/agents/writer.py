"""Content Writer Agent - Creates the actual content based on research and outline."""

from typing import Any

from langchain_core.messages import HumanMessage

from src.agents.base import BaseAgent


class WriterAgent(BaseAgent):
    """Agent responsible for writing the content."""

    name = "writer"
    description = "Creates engaging, high-quality content based on research and outline"

    system_prompt = """You are a world-class content writer with expertise in creating engaging, informative content.

Your writing is characterized by:
- Clear, compelling prose that captures attention
- Strong opening hooks that draw readers in
- Logical flow that guides readers through the content
- Strategic use of examples, analogies, and storytelling
- Action-oriented conclusions with clear takeaways

WRITING PRINCIPLES:
1. Show, don't tell - Use specific examples and stories
2. One idea per paragraph - Keep paragraphs focused and scannable
3. Use active voice - Makes content more engaging
4. Vary sentence length - Creates rhythm and maintains interest
5. Include transitions - Connect ideas smoothly
6. Write for skimmers - Use headers, bullets, and bold text strategically

TONE ADAPTATION:
- Professional: Authoritative but accessible, data-driven
- Casual: Conversational, relatable, uses contractions
- Educational: Clear explanations, step-by-step guidance
- Persuasive: Benefit-focused, addresses objections

Always write content that provides genuine value to the reader."""

    async def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """Write the content based on research and outline.

        Args:
            state: Current workflow state

        Returns:
            Updated state with written content
        """
        request = state.get("request")
        research = state.get("research")
        outline = state.get("outline")

        if not request:
            raise ValueError("No content request found in state")

        # Build the writing prompt
        writing_prompt = self._build_writing_prompt(request, research, outline)

        messages = [HumanMessage(content=writing_prompt)]
        response = await self.invoke(messages)
        draft_content = self._as_text(response.content)

        return {
            **state,
            "draft_content": draft_content,
            "status": "writing_complete",
            "messages": state.get("messages", []) + [response],
        }

    def _build_writing_prompt(self, request: Any, research: Any, outline: Any) -> str:
        """Build the writing prompt from available information.

        Args:
            request: Original content request
            research: Research results
            outline: Content outline

        Returns:
            Formatted writing prompt
        """
        prompt_parts = [
            f"Please write a {request.content_type.value} about: {request.topic}",
            f"\nTARGET LENGTH: Approximately {request.word_count} words",
            f"TONE: {request.tone}",
            f"LANGUAGE: {request.language}",
        ]

        if request.target_audience:
            prompt_parts.append(f"TARGET AUDIENCE: {request.target_audience}")

        if request.keywords:
            prompt_parts.append(f"KEYWORDS TO INCLUDE: {', '.join(request.keywords)}")

        if research:
            prompt_parts.append("\n--- RESEARCH FINDINGS ---")
            if research.key_facts:
                prompt_parts.append("Key Facts:")
                for fact in research.key_facts[:5]:
                    prompt_parts.append(f"  - {fact}")
            if research.statistics:
                prompt_parts.append("Statistics:")
                for stat in research.statistics[:3]:
                    prompt_parts.append(f"  - {stat}")

        if outline:
            prompt_parts.append("\n--- CONTENT OUTLINE ---")
            prompt_parts.append(f"Title: {outline.title}")
            prompt_parts.append(f"Hook: {outline.hook}")
            prompt_parts.append("Sections:")
            for section in outline.sections:
                prompt_parts.append(f"  - {section.get('header', 'Section')}")
                for point in section.get("points", []):
                    prompt_parts.append(f"    • {point}")

        if request.additional_instructions:
            prompt_parts.append(f"\nADDITIONAL INSTRUCTIONS: {request.additional_instructions}")

        prompt_parts.append("\n--- OUTPUT ---")
        prompt_parts.append(
            "Write the complete content now. Include proper formatting with headers (##), bullet points where appropriate, and ensure the content flows naturally."
        )

        return "\n".join(prompt_parts)
