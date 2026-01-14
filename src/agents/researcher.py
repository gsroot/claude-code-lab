"""Deep Researcher Agent - Gathers information and facts about the topic."""

from typing import Any

from langchain_core.messages import HumanMessage

from src.agents.base import BaseAgent
from src.models.content import ResearchResult


class ResearcherAgent(BaseAgent):
    """Agent responsible for deep research on the content topic."""

    name = "researcher"
    description = "Conducts thorough research to gather facts, statistics, and insights"

    system_prompt = """You are an expert researcher with exceptional skills in gathering and synthesizing information.

Your role is to:
1. Research the given topic thoroughly
2. Find credible sources, statistics, and expert opinions
3. Identify key facts that would make the content compelling
4. Discover unique angles and insights competitors might miss
5. Note any recent trends or developments

IMPORTANT GUIDELINES:
- Focus on accuracy and credibility of information
- Prioritize recent data (within last 2 years when possible)
- Look for surprising or counterintuitive facts that engage readers
- Identify potential controversy or debate points
- Find real examples and case studies

OUTPUT FORMAT:
Provide your research findings in a structured format with:
- Key Facts: Main factual points discovered
- Statistics: Relevant numbers and data points
- Expert Quotes: Notable quotes from authorities
- Sources: Where information was found
- Competitor Insights: What others are saying about this topic
- Unique Angles: Fresh perspectives not commonly covered"""

    async def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """Conduct research on the topic.

        Args:
            state: Current workflow state containing the content request

        Returns:
            Updated state with research results
        """
        request = state.get("request")
        if not request:
            raise ValueError("No content request found in state")

        # Construct the research prompt
        research_prompt = f"""Please conduct thorough research on the following topic:

TOPIC: {request.topic}
CONTENT TYPE: {request.content_type}
TARGET AUDIENCE: {request.target_audience or "General audience"}
LANGUAGE: {request.language}

Additional context: {request.additional_instructions or "None provided"}

Please gather:
1. At least 5 key facts about this topic
2. Relevant statistics and data points
3. Expert opinions or quotes
4. What competitors/others are writing about this
5. Any unique angles worth exploring

Focus on information that would resonate with {request.target_audience or "the general audience"}."""

        messages = [HumanMessage(content=research_prompt)]
        response = await self.invoke(messages)

        # Parse the research results
        research = self._parse_research(self._as_text(response.content))

        return {
            **state,
            "research": research,
            "status": "researching_complete",
            "messages": state.get("messages", []) + [response],
        }

    def _parse_research(self, content: str) -> ResearchResult:
        """Parse LLM response into structured research result.

        Args:
            content: Raw LLM response content

        Returns:
            Structured ResearchResult
        """
        # Simple parsing - in production, use structured output or more robust parsing
        result = ResearchResult()

        lines = content.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            lower_line = line.lower()

            if "key fact" in lower_line or "main fact" in lower_line:
                current_section = "facts"
            elif "statistic" in lower_line or "data" in lower_line:
                current_section = "statistics"
            elif "quote" in lower_line or "expert" in lower_line:
                current_section = "quotes"
            elif "source" in lower_line:
                current_section = "sources"
            elif "competitor" in lower_line or "insight" in lower_line:
                current_section = "competitors"
            elif line.startswith("-") or line.startswith("•") or line.startswith("*"):
                item = line.lstrip("-•* ").strip()
                if current_section == "facts":
                    result.key_facts.append(item)
                elif current_section == "statistics":
                    result.statistics.append(item)
                elif current_section == "quotes":
                    result.quotes.append(item)
                elif current_section == "sources":
                    result.sources.append({"text": item})
                elif current_section == "competitors":
                    result.competitor_insights.append(item)

        return result
