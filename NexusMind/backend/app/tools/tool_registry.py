"""
tool_registry.py — MCP-style tool registry and dispatcher.

Tools are registered with:
  - name: unique identifier
  - description: what the tool does (fed to Gemini function-calling schemas)
  - input_schema: dict describing accepted parameters
  - handler: async callable that executes the tool

Agents call tools via:  await tool_registry.call("web_search", query="...")
"""
from typing import Callable, Any, Optional
import asyncio


class ToolDefinition:
    """Metadata + handler for one MCP tool."""

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: dict,
        handler: Callable,
    ):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.handler = handler

    def to_gemini_function(self) -> dict:
        """Return a Gemini-compatible function declaration for tool-use prompting."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.input_schema,
            },
        }

    def to_tool_dict(self) -> dict:
        """Return a dict compatible with GeminiClient.generate_with_tools()."""
        return {
            "name":         self.name,
            "description":  self.description,
            "input_schema": self.input_schema,
            "handler":      self.handler,
        }


class ToolRegistry:
    """
    Central registry of all MCP-style tools available to agents.

    Usage:
        result = await tool_registry.call("web_search", query="FastAPI tutorial")
        result = await tool_registry.call("validate_yaml", content="...")
        result = await tool_registry.call("execute_python", code="print('hi')")
    """

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition):
        self._tools[tool.name] = tool

    def list_tools(self) -> list[dict]:
        """Return all registered tools as Gemini function declarations."""
        return [t.to_gemini_function() for t in self._tools.values()]

    def get_tool_defs(self, *names: str) -> list[dict]:
        """
        Return tool dicts compatible with GeminiClient.generate_with_tools()
        for the given tool names.  Missing names are silently skipped.
        """
        result = []
        for name in names:
            td = self._tools.get(name)
            if td:
                result.append(td.to_tool_dict())
        return result

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    async def call(self, name: str, **kwargs) -> dict:
        """
        Invoke a tool by name.
        Returns a dict with at least: { "tool": name, "success": bool, ... }
        """
        tool = self._tools.get(name)
        if not tool:
            return {"tool": name, "success": False, "error": f"Tool '{name}' not registered."}
        try:
            result = await tool.handler(**kwargs)
            if isinstance(result, dict):
                return {"tool": name, "success": True, **result}
            return {"tool": name, "success": True, "result": result}
        except Exception as exc:
            return {"tool": name, "success": False, "error": str(exc)}


# ── Singleton ─────────────────────────────────────────────────────────────────
tool_registry = ToolRegistry()


def bootstrap_tools():
    """Register all built-in MCP tools. Called at application startup."""
    from app.tools.web_search import web_search
    from app.tools.code_executor import execute_python
    from app.tools.yaml_validator import validate_yaml
    from app.tools.code_formatter import check_python_syntax, check_typescript_syntax
    from app.tools.file_writer import write_file, list_files, get_file
    from app.tools.web_scraper import scrape_url
    from app.tools.chart_renderer import generate_chart

    tool_registry.register(ToolDefinition(
        name="web_search",
        description="Search the web for information on a given query. Returns titles, URLs and snippets.",
        input_schema={
            "query":       {"type": "string", "description": "The search query"},
            "num_results": {"type": "integer", "description": "Max results (default 5)"},
        },
        handler=web_search,
    ))

    tool_registry.register(ToolDefinition(
        name="execute_python",
        description="Execute a Python code snippet in a sandboxed subprocess. Returns stdout/stderr.",
        input_schema={
            "code":    {"type": "string",  "description": "Python source code to run"},
            "timeout": {"type": "integer", "description": "Max execution seconds (default 10)"},
        },
        handler=execute_python,
    ))

    tool_registry.register(ToolDefinition(
        name="validate_yaml",
        description="Validate a YAML string for syntax correctness. Returns parsed data or error.",
        input_schema={
            "content": {"type": "string", "description": "YAML content to validate"},
        },
        handler=validate_yaml,
    ))

    tool_registry.register(ToolDefinition(
        name="check_python_syntax",
        description="Check a Python source string for syntax errors using the ast module.",
        input_schema={
            "code": {"type": "string", "description": "Python source code"},
        },
        handler=check_python_syntax,
    ))

    tool_registry.register(ToolDefinition(
        name="check_typescript_syntax",
        description="Perform lightweight TypeScript/TSX validation checks.",
        input_schema={
            "code": {"type": "string", "description": "TypeScript/TSX source code"},
        },
        handler=check_typescript_syntax,
    ))

    tool_registry.register(ToolDefinition(
        name="write_file",
        description="Stage a generated file in session shared memory for later assembly.",
        input_schema={
            "session_id": {"type": "string", "description": "Session identifier"},
            "filename":   {"type": "string", "description": "Relative file path"},
            "content":    {"type": "string", "description": "Full file content"},
        },
        handler=write_file,
    ))

    tool_registry.register(ToolDefinition(
        name="list_files",
        description="List all staged files in the session memory.",
        input_schema={
            "session_id": {"type": "string", "description": "Session identifier"},
        },
        handler=list_files,
    ))

    tool_registry.register(ToolDefinition(
        name="get_file",
        description="Retrieve a specific staged file from session memory by filename.",
        input_schema={
            "session_id": {"type": "string", "description": "Session identifier"},
            "filename":   {"type": "string", "description": "Relative file path to retrieve"},
        },
        handler=get_file,
    ))

    tool_registry.register(ToolDefinition(
        name="scrape_url",
        description=(
            "Fetch the full text content of a web page from a URL. "
            "Use after web_search to retrieve detailed information beyond snippets. "
            "Returns cleaned plain text (up to 8 000 chars)."
        ),
        input_schema={
            "url":     {"type": "string",  "description": "Full URL to fetch"},
            "timeout": {"type": "integer", "description": "Request timeout in seconds (default 10)"},
        },
        handler=scrape_url,
    ))

    tool_registry.register(ToolDefinition(
        name="generate_chart",
        description=(
            "Generate a chart image (PNG) using matplotlib and return it as a base64 data URI. "
            "Supports: bar, line, pie, scatter, histogram. "
            "data must be a JSON string: "
            '{"labels": [...], "values": [...]} for bar/line/pie, '
            '{"x": [...], "y": [...]} for scatter, '
            '{"values": [...]} for histogram.'
        ),
        input_schema={
            "chart_type": {"type": "string",  "description": "bar | line | pie | scatter | histogram"},
            "data":       {"type": "string",  "description": "JSON string of chart data"},
            "title":      {"type": "string",  "description": "Chart title"},
            "x_label":    {"type": "string",  "description": "X-axis label"},
            "y_label":    {"type": "string",  "description": "Y-axis label"},
        },
        handler=generate_chart,
    ))
