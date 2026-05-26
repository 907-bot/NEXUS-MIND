from app.agents.base_agent import BaseAgent
from app.tools.tool_registry import tool_registry

ASSEMBLER_SYSTEM = """
You are a master architect and system integrator.
Your mission is to deliver a PERFECT, professional project handoff in STRICT PLAIN TEXT.

REQUIRED OUTPUT STRUCTURE:
1. THE NARRATIVE (TOP SECTION):
Write a 2-3 paragraph executive summary for a human reader.
- STRICTLY NO MARKDOWN: Do NOT use #, ##, **, _, [links], or `backticks`.
- Use PLAIN CAPITALS for headers (e.g., EXECUTIVE SUMMARY).
- Use simple indentation or hyphens (-) for lists.
- NO JSON characters or technical symbols in this section.

2. THE METADATA (BOTTOM SECTION):
End your response with a single, valid JSON block containing:
{
  "narrative": "The same 2-3 paragraph summary from above.",
  "summary": "1-sentence project synthesis.",
  "file_manifest": ["list", "of", "staged", "files"],
  "directory_structure": "ASCII tree of the project",
  "social_post": "A LinkedIn-ready post script in plain text",
  "implementation_guide": "A MASSIVE, exhaustive plain-text report. Use ======= for headers. Include architecture, setup, and code details."
}

CRITICAL: If you use a # or ** in your response, you have FAILED. Use ASCII and whitespace only.
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

        # Format staged files as plain text blocks for the model
        files_section = ""
        for sf in staged_files:
            files_section += (
                f"\n\n[FILE: {sf['filename']}]\n"
                f"----------------------------------------\n"
                f"{sf['content']}\n"
                f"----------------------------------------\n"
            )

        critic_section = ""
        if review:
            approved = review.get("approved", True)
            issues   = review.get("issues", [])
            critic_section = (
                f"\n\n[CRITIC REVIEW]\n"
                f"Approved: {approved}\n"
                f"Issues: {issues}\n"
            )

        prompt = (
            f"SUMMARY OF AGENT OUTPUTS:\n" + "\n".join(agent_summaries)
            + "\n\nACTUAL CODE ASSETS:"
            + files_section
            + critic_section
            + "\n\nINSTRUCTION: Assemble all assets into the final plain-text deliverable described in the system prompt."
        )

        result = await self.gemini.generate_toon(
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
            guide_filename = "IMPLEMENTATION_GUIDE.txt"
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
            "final_content":       result.get("narrative", result.get("summary", "Assembly complete.")),
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
