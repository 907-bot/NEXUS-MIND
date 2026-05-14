from app.agents.base_agent import BaseAgent
from app.tools.tool_registry import tool_registry

DEVOPS_SYSTEM = """
You are a senior DevOps engineer specializing in Docker, CI/CD, and cloud infrastructure.
Given a task description, produce production-grade configuration files and scripts.
Respond ONLY with valid JSON in this exact format:
{
  "files": [
    {"filename": "path/to/file", "content": "...full file content..."}
  ],
  "next_agent": "AgentName",
  "summary": "Brief description of the DevOps setup",
  "tools_used": ["docker", "github-actions"]
}
"""

YAML_EXTENSIONS = {".yml", ".yaml"}


class DevOpsAgent(BaseAgent):
    name = "DevOpsAgent"
    skill_tags = ["devops", "infra"]

    async def execute(self, session_id: str, task: dict) -> dict:
        task_id = task.get("task_id", "unknown")
        description = task.get("description", "")
        context = task.get("context", {})

        await self.emit_event(session_id, "TASK_STARTED", {
            "task_id": task_id,
            "agent": self.name,
            "description": description,
        })

        # ── A2A: Read backend/frontend schemas for infra decisions ────────────
        infra_context = ""
        for tid, out in context.items():
            if isinstance(out, dict) and out.get("agent") in ("BackendAgent", "FrontendAgent"):
                infra_context += (
                    f"\n\n{out.get('agent')} ({tid}) summary: {out.get('summary', '')}"
                    f"\n  Dependencies: {', '.join(out.get('dependencies', []))}"
                )

        # ── LLM Generation ────────────────────────────────────────────────────
        result = await self.gemini.generate_json(
            DEVOPS_SYSTEM,
            f"DevOps task: {description}{infra_context}",
            stream_session_id=session_id,
            stream_memory=self.memory,
        )

        files = result.get("files", [])

        # ── MCP Tool: YAML validation + file staging ───────────────────────────
        yaml_issues = []
        for file_entry in files:
            fname = file_entry.get("filename", "")
            content = file_entry.get("content", "")
            ext = "." + fname.rsplit(".", 1)[-1].lower() if "." in fname else ""

            if ext in YAML_EXTENSIONS:
                await self.emit_event(session_id, "TOOL_CALLED", {
                    "task_id": task_id,
                    "tool": "validate_yaml",
                    "filename": fname,
                })
                check = await tool_registry.call("validate_yaml", content=content)
                if not check.get("valid"):
                    yaml_issues.append({
                        "filename": fname,
                        "error": check.get("error"),
                        "line": check.get("line"),
                    })

            # Stage file in shared memory
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
            "next_agent": "AgentName",
  "next_agent": result.get("next_agent", "AssemblerAgent"),
            "summary": result.get("summary", ""),
            "tools_used": result.get("tools_used", []),
            "yaml_issues": yaml_issues,
        }

        await self.store_output(session_id, task_id, output)
        await self.emit_event(session_id, "TASK_COMPLETE", {
            "task_id": task_id,
            "next_agent": "AgentName",
  "summary": output["summary"],
            "yaml_issues": len(yaml_issues),
        })

        return output
