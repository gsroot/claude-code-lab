"""MCP Client for connecting to MCP servers and loading tools."""

from typing import Any, cast

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from loguru import logger

from src.utils.config import settings


class MCPToolManager:
    """Manages connections to MCP servers and provides tools to agents.

    This class handles:
    - Connecting to multiple MCP servers
    - Loading and caching tools from servers
    - Providing tools to LangGraph agents
    """

    def __init__(self) -> None:
        """Initialize the MCP tool manager."""
        self._client: MultiServerMCPClient | None = None
        self._tools: list[BaseTool] = []
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize connections to all configured MCP servers."""
        if self._initialized:
            return

        logger.info("Initializing MCP connections...")

        # Configure MCP servers
        server_configs = cast(Any, self._get_server_configs())

        try:
            self._client = MultiServerMCPClient(server_configs)
            await self._client.__aenter__()
            self._tools = await self._client.get_tools()
            self._initialized = True

            logger.info(f"MCP initialized with {len(self._tools)} tools")
            for tool in self._tools:
                logger.debug(f"  - {tool.name}: {tool.description[:50]}...")

        except Exception as e:
            logger.error(f"Failed to initialize MCP: {e}")
            raise

    def _get_server_configs(self) -> dict[str, dict[str, Any]]:
        """Get MCP server configurations.

        Returns:
            Dictionary of server configs keyed by server name
        """
        configs = {}

        # Fetch server - for web content retrieval
        if settings.mcp_fetch_server:
            configs["fetch"] = {
                "command": "npx",
                "args": ["-y", "@anthropic/mcp-fetch"],
                "env": {},
            }

        # Memory server - for persistent knowledge
        if settings.mcp_memory_server:
            configs["memory"] = {
                "command": "npx",
                "args": ["-y", "@anthropic/mcp-memory"],
                "env": {},
            }

        return configs

    def get_tools(self) -> list[BaseTool]:
        """Get all available MCP tools.

        Returns:
            List of LangChain-compatible tools
        """
        if not self._initialized:
            logger.warning("MCP not initialized, returning empty tool list")
            return []
        return self._tools

    def get_tools_by_server(self, server_name: str) -> list[BaseTool]:
        """Get tools from a specific MCP server.

        Args:
            server_name: Name of the MCP server

        Returns:
            List of tools from that server
        """
        return [t for t in self._tools if t.name.startswith(f"{server_name}_")]

    async def close(self) -> None:
        """Close all MCP connections."""
        if self._client:
            await cast(Any, self._client.__aexit__)(None, None, None)
            self._client = None
            self._tools = []
            self._initialized = False
            logger.info("MCP connections closed")


# Global instance
mcp_manager = MCPToolManager()


async def get_mcp_tools() -> list[BaseTool]:
    """Get all available MCP tools, initializing if needed.

    Returns:
        List of available MCP tools
    """
    if not mcp_manager._initialized:
        await mcp_manager.initialize()
    return mcp_manager.get_tools()
