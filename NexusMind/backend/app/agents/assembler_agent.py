from app.agents.base_agent import BaseAgent
from app.tools.tool_registry import tool_registry

ASSEMBLER_SYSTEM = """
You are a master architect and system integrator.
Your job is to merge multiple agent outputs and generated source files.

Output Format (TOON - Token Oriented Object Notation):
1. **The Narrative**: Write a CONCISE, simple-text executive summary of the project.
2. **The Metadata**: End with a JSON block containing:
   - summary: 1-sentence synthesis.
   - file_manifest: List of all generated files.
   - directory_structure: ASCII tree.
   - social_post: LinkedIn script.
   - implementation_guide: THE FULL DETAILED MARKDOWN DOCUMENT (Implementation, API specs, Deployment, etc.). 
     This will be automatically converted into a downloadable 'IMPLEMENTATION_GUIDE.md'.

The 'implementation_guide' field must contain:
- Detailed technical breakdown.
- Architecture overview.
- Directory structure.
- API & Data Models.
- Deployment Guide.
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

        # ── Step 4: Extract and Stage the Implementation Guide ────────────────
        # We take the detailed markdown from the JSON and create a real file
        # so it's included in the "Download All" bundle.
        guide_content = result.get("implementation_guide", "")
        if guide_content:
            guide_filename = "IMPLEMENTATION_GUIDE.md"
            await tool_registry.call(
                "write_file", 
                session_id=session_id, 
                filename=guide_filename, 
                content=guide_content
            )
            # Add to staged files for the return object
            staged_files.append({"filename": guide_filename, "content": guide_content})
            staged_filenames.append(guide_filename)

        output = {
            "final_content":       result.get("_toon_narrative", result.get("summary", "Assembly complete.")),
            "summary":             result.get("summary", "Assembly complete."),
            "file_manifest":       staged_filenames,
            "directory_structure": result.get("directory_structure", ""),
            "social_post":         result.get("social_post", ""),
            "staged_files":        staged_files,
        }

        await self.memory.set(session_id, "final_output", output)
        await self.emit_event(session_id, "FINAL_OUTPUT", {
            "summary":             output["summary"],
            "files_assembled":     len(staged_files),
            "file_manifest":       output["file_manifest"],
            "directory_structure": output["directory_structure"],
            "social_post":         output["social_post"],
            "final_content":       output["final_content"],
        })

        return output
