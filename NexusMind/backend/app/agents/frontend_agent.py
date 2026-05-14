from app.agents.base_agent import BaseAgent
from app.tools.tool_registry import tool_registry

FRONTEND_SYSTEM = """
You are an expert frontend engineer specializing in React, Next.js 14, TypeScript, and Tailwind CSS.
Given a task description and any API contracts from the backend, produce production-ready frontend code.
Respond ONLY with valid JSON in this exact format:
{
  "files": [
    {"filename": "components/ComponentName.tsx", "content": "...full code..."}
  ],
  "next_agent": "AgentName",
  "summary": "Brief description of what was built",
  "dependencies": ["react", "tailwindcss"]
}
"""


class FrontendAgent(BaseAgent):
    name = "FrontendAgent"
    skill_tags = ["frontend", "ui"]

    async def execute(self, session_id: str, task: dict) -> dict:
        task_id = task.get("task_id", "unknown")
        description = task.get("description", "")
        context = task.get("context", {})

        await self.emit_event(session_id, "TASK_STARTED", {
            "task_id": task_id,
            "agent": self.name,
            "description": description,
        })

        # ── A2A Step 1: Send INFORMATION_REQUEST to BackendAgent ──────────────
        # Ask BackendAgent for any API contracts/endpoint schemas we need.
        # The request is persisted in Redis — if BackendAgent runs (or has run),
        # it will produce an INFORMATION_RESPONSE that we can read.
        await self.send_a2a_message(
            session_id,
            to_agent="BackendAgent",
            msg_type="INFORMATION_REQUEST",
            payload={
                "request": (
                    "What are the REST API endpoint URLs, request schemas, and response "
                    "schemas this frontend task should integrate with? "
                    f"Frontend task: {description}"
                ),
                "task_ref": task_id,
            },
        )

        # ── A2A Step 2: Read any INFORMATION_RESPONSE already sent back ───────
        # BackendAgent may have already completed and responded (e.g. from a
        # previous phase with a dependency).
        a2a_api_context = ""
        a2a_responses = await self.read_a2a_responses(session_id)
        if a2a_responses:
            a2a_api_context = "\n\nA2A responses from BackendAgent:\n"
            for resp in a2a_responses:
                a2a_api_context += (
                    f"  [{resp['from_agent']}]: "
                    f"{resp['payload'].get('response', '')[:800]}\n"
                )

        # ── Context from completed tasks (direct memory access) ───────────────
        api_context = ""
        for tid, out in context.items():
            if isinstance(out, dict) and out.get("agent") == "BackendAgent":
                api_context += f"\n\nBackend output ({tid}) — {out.get('summary', '')}"
                contracts = out.get("api_contracts", [])
                if contracts:
                    api_context += f"\nAPI contracts: {contracts}"
                for f in out.get("files", []):
                    api_context += f"\n  - {f.get('filename', '')}"

        # ── LLM Generation ────────────────────────────────────────────────────
        result = await self.gemini.generate_json(
            FRONTEND_SYSTEM,
            f"Task: {description}{api_context}{a2a_api_context}",
            stream_session_id=session_id,
            stream_memory=self.memory,
        )

        files = result.get("files", [])

        # ── MCP Tool: TypeScript syntax check + file staging ──────────────────
        ts_issues = []
        for file_entry in files:
            fname = file_entry.get("filename", "")
            content = file_entry.get("content", "")

            if fname.endswith((".ts", ".tsx")):
                await self.emit_event(session_id, "TOOL_CALLED", {
                    "task_id": task_id,
                    "tool": "check_typescript_syntax",
                    "filename": fname,
                })
                check = await tool_registry.call("check_typescript_syntax", code=content)
                if not check.get("valid"):
                    ts_issues.extend(check.get("issues", []))

            # Stage every file in shared memory
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
            "next_agent": "AgentName",
  "next_agent": result.get("next_agent", "AssemblerAgent"),
            "summary": result.get("summary", ""),
            "dependencies": result.get("dependencies", []),
            "ts_issues": ts_issues,
        }

        await self.store_output(session_id, task_id, output)

        # ── A2A Step 3: Respond to any requests directed at FrontendAgent ─────
        await self.respond_to_a2a_requests(
            session_id,
            current_output=output,
            system_context=f"Files generated: {[f['filename'] for f in files]}",
        )

        await self.emit_event(session_id, "TASK_COMPLETE", {
            "task_id": task_id,
            "next_agent": "AgentName",
  "summary": output["summary"],
            "files_generated": len(files),
        })

        return output
