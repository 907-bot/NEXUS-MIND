import asyncio
import os
import logging
from typing import Dict, List, Optional, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

logger = logging.getLogger(__name__)

class MCPManager:
    """
    Manages connections to external MCP servers and registers their tools
    into the NexusMind tool registry.
    """

    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self._exit_stack = AsyncExitStack()
        self._is_started = False

    async def start(self):
        """Initialize connections to configured MCP servers."""
        if self._is_started:
            return
        
        # Example configurations for "free" or common MCP servers
        # In a real app, these would come from a config file or DB
        server_configs = [
            {
                "name": "google_search",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-google-search"],
                "env": {
                    "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY", ""),
                    "GOOGLE_SEARCH_ENGINE_ID": os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")
                }
            },
            {
                "name": "sequential_thinking",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
            },
            {
                "name": "fetch",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-fetch"],
            },
            {
                "name": "filesystem",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", os.getcwd()],
            }
        ]

        for config in server_configs:
            # Skip if missing required env vars for authenticated servers
            if config["name"] == "google_search" and not os.getenv("GOOGLE_API_KEY"):
                logger.warning(f"⚠️ Skipping {config['name']} - GOOGLE_API_KEY not set.")
                continue

            try:
                await self._connect_to_server(
                    config["name"], 
                    config["command"], 
                    config["args"], 
                    config.get("env")
                )
                logger.info(f"✅ Connected to MCP server: {config['name']}")
            except Exception as e:
                logger.error(f"❌ Failed to connect to MCP server {config['name']}: {e}")

        self._is_started = True

    async def _connect_to_server(self, name: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None):
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env={**os.environ, **(env or {})}
        )

        # Enter the stdio_client context
        read, write = await self._exit_stack.enter_async_context(stdio_client(server_params))
        # Enter the ClientSession context
        session = await self._exit_stack.enter_async_context(ClientSession(read, write))
        
        await session.initialize()
        self.sessions[name] = session
        
        # Register tools from this server into the global tool registry
        await self._register_tools(name, session)

    async def _register_tools(self, server_name: str, session: ClientSession):
        from app.tools.tool_registry import ToolDefinition, tool_registry
        
        tools_response = await session.list_tools()
        for tool in tools_response.tools:
            # We prefix tool names to avoid collisions: servername_toolname
            mcp_tool_name = f"{server_name}_{tool.name}"
            
            # Define a closure that captures the session and tool name
            async def create_handler(s: ClientSession, t_name: str):
                async def handler(**kwargs):
                    result = await s.call_tool(t_name, kwargs)
                    return {
                        "content": [c.model_dump() for c in result.content],
                        "is_error": result.isError
                    }
                return handler

            handler = await create_handler(session, tool.name)
            
            tool_registry.register(ToolDefinition(
                name=mcp_tool_name,
                description=f"[MCP:{server_name}] {tool.description}",
                input_schema=tool.inputSchema,
                handler=handler
            ))

    async def stop(self):
        """Gracefully shut down all MCP connections."""
        await self._exit_stack.aclose()
        self.sessions.clear()
        self._is_started = False
        logger.info("🛑 All MCP sessions closed.")

# Singleton instance
mcp_manager = MCPManager()
