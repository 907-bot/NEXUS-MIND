from app.agents.base_agent import BaseAgent
from app.tools.tool_registry import tool_registry

ASSEMBLER_SYSTEM = """
You are a master architect and system integrator.
Your job is to merge multiple agent outputs and all generated source files into a
single, cohesive, professional deliverable written as a comprehensive markdown document.

The document should include:
1. An executive summary of what was built
2. Architecture overview
3. All generated source files (fenced code blocks with correct language tags)
4. API contracts / endpoint reference
5. Data models and schemas
6. Deployment and dependency notes
7. Any known issues flagged by the Critic

Respond ONLY with valid JSON in this exact format:
{
  "final_content": "# Project Title\\n\\n## Summary\\n...",
  "summary": "Unified all components into a final report",
  "file_manifest": ["path/to/file1.py", "path/to/file2.tsx"]
}
"""


class AssemblerAgent(BaseAgent):
    name = "AssemblerAgent"
    skill_tags = ["assembly"]

    async def execute(self, session_id: str, task: dict) -> dict:
        outputs = task.get("outputs", {})
        review  = task.get("review", {})

        await self.emit_event(session_id, "ASSEMBLY_STARTED", {
            "agent_outputs_count": len(outputs),
        })

        # ── MCP Step 1: Retrieve every file staged by agents ─────────────────
        # Agents (Backend, Frontend, DevOps…) staged files via write_file.
        # The Assembler must retrieve them all so Gemini gets actual code content,
        # not just summaries.
        await self.emit_event(session_id, "TOOL_CALLED", {
            "tool": "list_files",
            "session_id": session_id,
        })
        listing = await tool_registry.call("list_files", session_id=session_id)
        staged_filenames: list[str] = listing.get("files", [])

        staged_files: list[dict] = []
        for fname in staged_filenames:
            await self.emit_event(session_id, "TOOL_CALLED", {
                "tool": "get_file",
                "filename": fname,
            })
            file_result = await tool_registry.call(
                "get_file",
                session_id=session_id,
                filename=fname,
            )
            if file_result.get("success") and file_result.get("content"):
                staged_files.append({
                    "filename": fname,
                    "content": file_result["content"],
                })

        # ── Build a structured prompt ─────────────────────────────────────────
        # Summarise each agent's output (avoid sending full code twice)
        agent_summaries = []
        for tid, out in outputs.items():
            if isinstance(out, dict):
                agent_summaries.append(
                    f"[{out.get('agent', 'Unknown')} / {tid}]: {out.get('summary', '')}"
                )

        # Format staged files as fenced code blocks for Gemini
        files_section = ""
        for sf in staged_files:
            ext = sf["filename"].rsplit(".", 1)[-1] if "." in sf["filename"] else "text"
            files_section += (
                f"\n\n### {sf['filename']}\n```{ext}\n{sf['content']}\n```"
            )

        critic_section = ""
        if review:
            approved = review.get("approved", True)
            issues   = review.get("issues", [])
            critic_section = (
                f"\n\nCritic review — approved: {approved}. "
                f"Issues: {issues}"
            )

        prompt = (
            f"Agent output summaries:\n" + "\n".join(agent_summaries)
            + files_section
            + critic_section
            + "\n\nAssemble all of the above into the final deliverable."
        )

        result = await self.gemini.generate_json(
            ASSEMBLER_SYSTEM,
            prompt,
            stream_session_id=session_id,
            stream_memory=self.memory,
        )

        output = {
            "final_content":  result.get("final_content", ""),
            "summary":        result.get("summary", ""),
            "file_manifest":  result.get("file_manifest", staged_filenames),
            "staged_files":   staged_files,
        }

        await self.memory.set(session_id, "final_output", output)
        await self.emit_event(session_id, "FINAL_OUTPUT", {
            "summary":        output["summary"],
            "files_assembled": len(staged_files),
            "file_manifest":  output["file_manifest"],
            "final_content":  output["final_content"],
        })

        return output
