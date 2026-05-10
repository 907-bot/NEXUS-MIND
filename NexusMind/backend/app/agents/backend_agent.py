from app.agents.base_agent import BaseAgent
from app.tools.tool_registry import tool_registry

BACKEND_SYSTEM = """
You are an expert backend engineer specializing in Python, FastAPI, PostgreSQL, and REST APIs.
Given a task description, produce production-ready backend code.
Respond ONLY with valid JSON in this exact format:
{
  "files": [
    {"filename": "path/to/file.py", "content": "...full code..."}
  ],
  "summary": "Brief description of what was built",
  "api_contracts": [
    {
      "endpoint": "POST /api/orders",
      "request_schema": {"order_id": "str", "items": "list"},
      "response_schema": {"order_id": "str", "status": "str", "total": "float"}
    }
  ],
  "dependencies": ["fastapi", "sqlalchemy"]
}
"""


class BackendAgent(BaseAgent):
    name = "BackendAgent"
    skill_tags = ["backend", "database", "api"]

    async def execute(self, session_id: str, task: dict) -> dict:
        task_id = task.get("task_id", "unknown")
        description = task.get("description", "")
        context = task.get("context", {})

        await self.emit_event(session_id, "TASK_STARTED", {
            "task_id": task_id,
            "agent": self.name,
            "description": description,
        })

        # ── A2A Step 1: Read INFORMATION_RESPONSE replies from prior requests ─
        # If this agent sent an INFORMATION_REQUEST in a previous task, check
        # whether the target agent has responded and include that in context.
        a2a_responses = await self.read_a2a_responses(session_id)
        a2a_context = ""
        if a2a_responses:
            a2a_context = "\n\nA2A responses received from peer agents:\n"
            for resp in a2a_responses:
                a2a_context += (
                    f"  From {resp['from_agent']}: "
                    f"{resp['payload'].get('response', '')[:500]}\n"
                )

        # ── Context from previously completed tasks ───────────────────────────
        context_summary = ""
        if context:
            relevant = []
            for tid, out in context.items():
                if isinstance(out, dict) and out.get("agent") in ("BackendAgent", "ResearchAgent"):
                    relevant.append(
                        f"[{out.get('agent')} / {tid}]: {out.get('summary', '')}"
                    )
            if relevant:
                context_summary = "\n\nContext from previous tasks:\n" + "\n".join(relevant)

        # ── LLM Generation ────────────────────────────────────────────────────
        result = await self.gemini.generate_json(
            BACKEND_SYSTEM,
            f"Task: {description}{context_summary}{a2a_context}",
        )

        files = result.get("files", [])
        api_contracts = result.get("api_contracts", [])

        # ── MCP Tool: Python syntax check + file staging ──────────────────────
        syntax_issues = []
        for file_entry in files:
            fname = file_entry.get("filename", "")
            content = file_entry.get("content", "")
            if fname.endswith(".py"):
                await self.emit_event(session_id, "TOOL_CALLED", {
                    "task_id": task_id,
                    "tool": "check_python_syntax",
                    "filename": fname,
                })
                check = await tool_registry.call("check_python_syntax", code=content)
                if not check.get("valid"):
                    syntax_issues.append({
                        "filename": fname,
                        "error": check.get("error"),
                        "line": check.get("line"),
                    })

            # Stage every file in shared memory for the Assembler to retrieve
            await self.emit_event(session_id, "TOOL_CALLED", {
                "task_id": task_id,
                "tool": "write_file",
                "filename": fname,
            })
            await tool_registry.call(
                "write_file",
                session_id=session_id,
                filename=fname,
                content=content,
            )

        output = {
            "task_id": task_id,
            "agent": self.name,
            "files": files,
            "api_contracts": api_contracts,
            "summary": result.get("summary", ""),
            "dependencies": result.get("dependencies", []),
            "syntax_issues": syntax_issues,
        }

        await self.store_output(session_id, task_id, output)

        # ── A2A Step 2: Respond to any pending INFORMATION_REQUEST messages ───
        # FrontendAgent (and others) may have asked about the API structure while
        # this agent was running.  Now that we have a concrete output, answer them.
        await self.respond_to_a2a_requests(
            session_id,
            current_output=output,
            system_context=(
                f"API contracts generated: {api_contracts}\n"
                f"Files generated: {[f['filename'] for f in files]}"
            ),
        )

        await self.emit_event(session_id, "TASK_COMPLETE", {
            "task_id": task_id,
            "summary": output["summary"],
            "files_generated": len(files),
            "api_contracts": len(api_contracts),
            "syntax_issues": len(syntax_issues),
        })

        return output
