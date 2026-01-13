"""Base agent class for Content Mate."""

from abc import ABC, abstractmethod
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, SystemMessage
from loguru import logger

from src.utils.config import settings


class BaseAgent(ABC):
    """Base class for all ContentMate agents."""

    name: str = "base_agent"
    description: str = "Base agent"
    system_prompt: str = "You are a helpful AI assistant."

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.7,
        tools: list[Any] | None = None,
    ):
        """Initialize the agent.

        Args:
            model: LLM model to use
            temperature: Sampling temperature
            tools: List of tools available to the agent
        """
        self.model_name = model or settings.default_llm_model
        self.temperature = temperature
        self.tools = tools or []

        self.llm = ChatAnthropic(
            model=self.model_name,
            temperature=self.temperature,
            api_key=settings.anthropic_api_key,
            max_tokens=settings.max_tokens_per_request,
        )

        if self.tools:
            self.llm = self.llm.bind_tools(self.tools)

        logger.info(f"Initialized {self.name} with model {self.model_name}")

    def get_system_message(self) -> SystemMessage:
        """Get the system message for this agent."""
        return SystemMessage(content=self.system_prompt)

    @abstractmethod
    async def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """Process the current state and return updated state.

        Args:
            state: Current workflow state

        Returns:
            Updated state dict
        """
        pass

    async def invoke(self, messages: list[BaseMessage]) -> BaseMessage:
        """Invoke the LLM with messages.

        Args:
            messages: List of messages to send

        Returns:
            LLM response message
        """
        full_messages = [self.get_system_message()] + messages
        response = await self.llm.ainvoke(full_messages)
        logger.debug(f"{self.name} response: {response.content[:200]}...")
        return response

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, model={self.model_name})"
