import asyncio
import os
import logging
from typing import Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.config import settings

logger = logging.getLogger(__name__)

class MCPManager:
    """
    Manages connections to external MCP servers and registers their tools
    into the NexusMind tool registry.
    """

    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self._tasks: List[asyncio.Task] = []
        self._is_started = False

    async def start(self):
        """Initialize connections to configured MCP servers."""
        if self._is_started:
            return
        
        # Use values from settings (which loaded the .env)
        google_key = os.getenv("GOOGLE_API_KEY") or getattr(settings, "GOOGLE_API_KEY", None)
        google_cx = os.getenv("GOOGLE_SEARCH_ENGINE_ID") or getattr(settings, "GOOGLE_SEARCH_ENGINE_ID", None)

        # Windows requires cmd /c or npx.cmd for subprocess calls
        if os.name == "nt":
            command = "cmd"
            base_args = ["/c", "npx", "-y"]
        else:
            command = "npx"
            base_args = ["-y"]

        server_configs = [
            {
                "name": "google_search",
                "command": command,
                "args": base_args + ["@mcp-for-dev/mcp-google-search"],
                "env": {
                    "GOOGLE_API_KEY": google_key,
                    "GOOGLE_SEARCH_ENGINE_ID": google_cx
                }
            },
            {
                "name": "sequential_thinking",
                "command": command,
                "args": base_args + ["@modelcontextprotocol/server-sequential-thinking"],
            }
        ]

        for config in server_configs:
            # Skip if missing required env vars for authenticated servers
            # Check for both None and empty string
            if config["name"] == "google_search":
                current_key = config["env"]["GOOGLE_API_KEY"]
                if not current_key or len(current_key.strip()) < 5:
                    logger.warning(f"⚠️ Skipping {config['name']} - GOOGLE_API_KEY is empty or too short in .env")
                    continue

            # Start each server in its own background task
            task = asyncio.create_task(self._run_server(config))
            self._tasks.append(task)

        self._is_started = True

    async def _run_server(self, config: dict):
        """Persistent task to maintain a server connection."""
        import shutil
        name = config["name"]
        logger.info(f"🚀 Starting connection to MCP server: {name}...")
        
        # Resolve full path to the command for Windows reliability
        command_path = shutil.which(config["command"])
        if not command_path:
            logger.error(f"❌ MCP server {name} failed: Command '{config['command']}' not found in PATH.")
            return

        server_params = StdioServerParameters(
            command=command_path,
            args=config["args"],
            env={**os.environ, **config.get("env", {})}
        )

        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Add a timeout so it doesn't hang forever on slow networks
                    await asyncio.wait_for(session.initialize(), timeout=30.0)
                    self.sessions[name] = session
                    
                    # Register tools
                    await self._register_tools(name, session)
                    logger.info(f"✅ Connected to MCP server: {name}")
                    
                    # Keep the task alive until the session ends or app shuts down
                    while True:
                        await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info(f"Stopping MCP server: {name}")
        except ExceptionGroup as eg:
            # Unwrap anyio ExceptionGroup to see the real cause
            for e in eg.exceptions:
                logger.error(f"❌ MCP server {name} failed. Real Cause: {type(e).__name__}: {e}")
        except Exception as e:
            logger.error(f"❌ MCP server {name} failed to start. Error: {type(e).__name__}: {e}")
        finally:
            self.sessions.pop(name, None)

    async def _register_tools(self, server_name: str, session: ClientSession):
        from app.tools.tool_registry import ToolDefinition, tool_registry
        
        # Retry logic for tool registration as some servers take time to be ready
        max_retries = 3
        for attempt in range(max_retries):
            try:
                tools_response = await session.list_tools()
                for tool in tools_response.tools:
                    mcp_tool_name = f"{server_name}_{tool.name}"
                    
                    async def create_handler(s: ClientSession, t_name: str):
                        async def handler(**kwargs):
                            res = await s.call_tool(t_name, kwargs)
                            return {
                                "content": [c.model_dump() for c in res.content],
                                "is_error": res.isError
                            }
                        return handler

                    handler = await create_handler(session, tool.name)
                    
                    tool_registry.register(ToolDefinition(
                        name=mcp_tool_name,
                        description=f"[MCP:{server_name}] {tool.description}",
                        input_schema=tool.inputSchema,
                        handler=handler
                    ))
                # Success!
                logger.info(f"✅ Registered {len(tools_response.tools)} tools from MCP server: {server_name}")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Retrying tool registration for {server_name} (attempt {attempt+2}/{max_retries})...")
                    await asyncio.sleep(2)
                else:
                    logger.error(f"Failed to register tools for {server_name} after {max_retries} attempts: {e}")

    async def stop(self):
        """Gracefully shut down all MCP connections."""
        for task in self._tasks:
            task.cancel()
        
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
            
        self.sessions.clear()
        self._tasks.clear()
        self._is_started = False
        logger.info("🛑 All MCP sessions closed.")

# Singleton instance
mcp_manager = MCPManager()

# Singleton instance
mcp_manager = MCPManager()
