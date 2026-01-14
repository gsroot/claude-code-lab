"""Editor Agent - Polishes and improves the written content."""

from typing import Any

from langchain_core.messages import HumanMessage

from src.agents.base import BaseAgent


class EditorAgent(BaseAgent):
    """Agent responsible for editing and polishing content."""

    name = "editor"
    description = "Reviews, edits, and polishes content for quality and clarity"

    system_prompt = """You are an expert editor with years of experience polishing content for top publications.

Your editing focuses on:
1. CLARITY: Ensure every sentence is clear and easy to understand
2. FLOW: Improve transitions and logical progression
3. ENGAGEMENT: Strengthen hooks, examples, and calls to action
4. ACCURACY: Verify claims are properly supported
5. GRAMMAR: Fix any grammatical or spelling errors
6. CONCISENESS: Remove redundancy without losing meaning

EDITING PROCESS:
1. First pass: Read for overall structure and flow
2. Second pass: Line-by-line editing for clarity and style
3. Third pass: Proofread for grammar, spelling, punctuation
4. Final pass: Ensure the content delivers on its promise

STYLE GUIDELINES:
- Remove filler words (very, really, just, actually)
- Replace passive voice with active voice
- Break up long sentences
- Ensure consistent tone throughout
- Verify all facts and claims are substantiated
- Check that headers accurately reflect content
- Ensure strong opening and closing

OUTPUT:
Provide the fully edited content, maintaining the original structure but with improvements throughout."""

    async def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """Edit and polish the draft content.

        Args:
            state: Current workflow state with draft content

        Returns:
            Updated state with edited content
        """
        request = state.get("request")
        draft_content = state.get("draft_content")

        if not request:
            raise ValueError("No content request found in state")

        if not draft_content:
            raise ValueError("No draft content found in state")

        # Build the editing prompt
        editing_prompt = f"""Please edit and polish the following content.

ORIGINAL REQUIREMENTS:
- Topic: {request.topic}
- Tone: {request.tone}
- Target audience: {request.target_audience or "General"}
- Target word count: {request.word_count} words

CONTENT TO EDIT:
{draft_content}

--- EDITING INSTRUCTIONS ---
1. Improve clarity and readability
2. Strengthen the opening hook
3. Ensure smooth transitions between sections
4. Fix any grammatical errors
5. Remove redundant phrases
6. Verify the tone is consistent with "{request.tone}"
7. Ensure the conclusion has a strong call-to-action
8. Keep approximately the same length

Please provide the fully edited content."""

        messages = [HumanMessage(content=editing_prompt)]
        response = await self.invoke(messages)
        edited_content = self._as_text(response.content)

        return {
            **state,
            "content": edited_content,
            "status": "editing_complete",
            "messages": state.get("messages", []) + [response],
        }
