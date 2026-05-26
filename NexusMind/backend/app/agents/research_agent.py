from app.agents.base_agent import BaseAgent
from app.tools.tool_registry import tool_registry

RESEARCH_SYSTEM = """
You are a senior research analyst. Given a research topic or question, you have access
to web search results to ground your analysis in real data.
Produce structured, accurate, factual research.

Your response should follow the TOON (Token Oriented Object Notation) format:
1. Write a comprehensive research report in markdown (analysis, insights, deep-dive).
2. End your response with a small JSON block for structured metadata.

The JSON block must have:
- findings: list of strings (key takeaways)
- sources: list of strings (URLs or references)
- next_agent: string (The name of the next agent: [BackendAgent, FrontendAgent, DataAgent, DevOpsAgent, ContentAgent, CriticAgent, AssemblerAgent])
- summary: string (2-3 sentence executive summary)
- recommendations: list of strings (actionable next steps)

Example Output:
# Research: [Topic]
... detailed analysis ...

{
  "findings": ["...", "..."],
  "sources": ["...", "..."],
  "next_agent": "BackendAgent",
  "summary": "...",
  "recommendations": ["...", "..."]
}
"""


class ResearchAgent(BaseAgent):
    name = "ResearchAgent"
    skill_tags = ["research"]

    async def execute(self, session_id: str, task: dict) -> dict:
        task_id = task.get("task_id", "unknown")
        description = task.get("description", "")

        await self.emit_event(session_id, "TASK_STARTED", {
            "task_id": task_id,
            "agent": self.name,
            "description": description,
        })

        # ── MCP Tool 1: Web Search ────────────────────────────────────────────
        await self.emit_event(session_id, "TOOL_CALLED", {
            "task_id": task_id, "tool": "web_search", "query": description,
        })
        search_result = await tool_registry.call("web_search", query=description, num_results=5)

        # ── MCP Tool 2: Web Scraper — fetch full content of top results ───────
        # Retrieve detailed text from the top 2 URLs to give Gemini richer
        # source material than snippets alone.
        scraped_pages: list[dict] = []
        if search_result.get("success"):
            top_urls = [r["url"] for r in search_result.get("results", [])[:2]]
            for url in top_urls:
                await self.emit_event(session_id, "TOOL_CALLED", {
                    "task_id": task_id, "tool": "scrape_url", "url": url,
                })
                page = await tool_registry.call("scrape_url", url=url, timeout=10)
                if page.get("success") and page.get("text_content"):
                    scraped_pages.append(page)

        # Build enriched prompt with search snippets + scraped full content
        search_context = ""
        if search_result.get("success") and search_result.get("results"):
            lines = [
                f"- [{r['title']}]({r['url']}): {r['snippet']}"
                for r in search_result["results"]
            ]
            search_context = "\n\nWeb search results:\n" + "\n".join(lines)

        scraped_context = ""
        if scraped_pages:
            scraped_context = "\n\nFull page content from top sources:\n"
            for p in scraped_pages:
                scraped_context += (
                    f"\n### {p['title']} ({p['url']})\n"
                    f"{p['text_content'][:3000]}\n"   # 3k chars per page
                )

        if not search_context and not scraped_context:
            search_context = "\n\n(Web search not available — using knowledge base.)"

        # ── A2A: Check if other agents have shared relevant context ───────────
        a2a_messages = await self.read_a2a_messages(session_id)
        a2a_context = ""
        if a2a_messages:
            a2a_context = "\n\nContext from other agents:\n" + "\n".join(
                f"- [{m['from_agent']}]: {m['payload']}"
                for m in a2a_messages
            )

        # ── LLM Generation ────────────────────────────────────────────────────
        result = await self.gemini.generate_toon(
            RESEARCH_SYSTEM,
            f"Research topic: {description}{search_context}{scraped_context}{a2a_context}",
            stream_session_id=session_id,
            stream_memory=self.memory,
        )

        output = {
            "task_id": task_id,
            "agent": self.name,
            "findings": result.get("findings", []),
            "sources": result.get("sources", []),
            "next_agent": result.get("next_agent", "AssemblerAgent"),
            "summary": result.get("summary", ""),
            "content": result.get("_toon_narrative", ""),
            "recommendations": result.get("recommendations", []),
            "search_results_used": len(search_result.get("results", [])),
            "pages_scraped": len(scraped_pages),
        }

        await self.store_output(session_id, task_id, output)
        await self.emit_event(session_id, "TASK_COMPLETE", {
            "task_id": task_id,
            "next_agent": output["next_agent"],
            "summary": output["summary"],
        })

        return output
