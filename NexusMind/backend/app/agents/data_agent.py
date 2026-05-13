from app.agents.base_agent import BaseAgent
from app.tools.tool_registry import tool_registry

DATA_SYSTEM = """
You are an expert data scientist and analyst with access to two tools:

  • web_search(query, num_results)   — search the web for datasets, benchmarks, research
  • execute_python(code, timeout)    — run Python (pandas, numpy, statistics) in a sandbox

Use these tools to gather real data and validate your SQL / pandas code before producing output.
After all tool calls are complete, respond ONLY with valid JSON:
{
  "analysis":            "Detailed written analysis",
  "insights":            ["key insight 1", "key insight 2"],
  "schema_suggestions":  ["suggestion 1"],
  "sql_queries":         [{"description": "...", "sql": "SELECT ..."}],
  "validated_code":      [{"description": "...", "code": "...", "output": "..."}],
  "chart_recommendations": ["chart type: description"],
  "summary":             "Executive summary"
}
"""


class DataAgent(BaseAgent):
    name = "DataAgent"
    skill_tags = ["data", "analytics"]

    async def execute(self, session_id: str, task: dict) -> dict:
        task_id    = task.get("task_id", "unknown")
        description = task.get("description", "")
        context    = task.get("context", {})

        await self.emit_event(session_id, "TASK_STARTED", {
            "task_id":     task_id,
            "agent":       self.name,
            "description": description,
        })

        # ── A2A: read any peer context (e.g. BackendAgent DB schema) ──────────
        a2a_responses = await self.read_a2a_responses(session_id)
        peer_context = ""
        if a2a_responses:
            peer_context = "\n\nPeer agent context:\n"
            for resp in a2a_responses:
                peer_context += f"  [{resp['from_agent']}]: {resp['payload'].get('response', '')[:400]}\n"

        context_summary = ""
        if context:
            for tid, out in context.items():
                if isinstance(out, dict) and out.get("agent") in ("BackendAgent", "ResearchAgent"):
                    context_summary += f"\n[{out.get('agent')} / {tid}]: {out.get('summary', '')}"

        # ── Build tool_definitions for generate_with_tools() ─────────────────
        tool_defs = tool_registry.get_tool_defs("web_search", "execute_python")

        user_message = (
            f"Data task: {description}"
            f"{context_summary}"
            f"{peer_context}"
        )

        # ── Native Gemini function calling ────────────────────────────────────
        # Gemini decides which tools to call, calls them, gets results, then
        # produces the final JSON output.
        tool_call_log: list[dict] = []

        if tool_defs:
            raw_text, tool_call_log = await self.gemini.generate_with_tools(
                DATA_SYSTEM,
                user_message,
                tool_defs,
            )
            # Emit each tool call as an observable event
            for tc in tool_call_log:
                await self.emit_event(session_id, "TOOL_CALLED", {
                    "task_id": task_id,
                    "tool":    tc["tool"],
                    "args":    tc["args"],
                })

            # parse JSON from the final text response
            import json, re
            clean = re.sub(r"```json|```", "", raw_text).strip()
            try:
                result = json.loads(clean)
            except Exception:
                # Fallback: treat the raw text as the analysis
                result = {
                    "analysis": raw_text,
                    "insights": [],
                    "schema_suggestions": [],
                    "sql_queries": [],
                    "validated_code": [],
                    "chart_recommendations": [],
                    "summary": raw_text[:200],
                }
        else:
            # No tools registered yet — pure LLM fallback
            result = await self.gemini.generate_json(
                DATA_SYSTEM,
                user_message,
                stream_session_id=session_id,
                stream_memory=self.memory,
            )
            tool_call_log = []

        # ── MCP: validate SQL + generate charts ───────────────────────────────
        validated_queries = []
        for q in result.get("sql_queries", []):
            sql = q.get("sql", "")
            if sql.strip().upper().startswith("SELECT"):
                validation_code = (
                    "import sqlite3\n"
                    "conn = sqlite3.connect(':memory:')\n"
                    "try:\n"
                    f"    conn.execute({repr(sql)})\n"
                    "    print('VALID')\n"
                    "except Exception as e:\n"
                    "    print(f'INVALID: {e}')\n"
                )
                await self.emit_event(session_id, "TOOL_CALLED", {
                    "task_id": task_id, "tool": "execute_python",
                    "purpose": f"SQL validation: {q.get('description', '')}",
                })
                vr = await tool_registry.call("execute_python", code=validation_code, timeout=5)
                stdout = vr.get("stdout", "").strip()
                validated_queries.append({
                    **q, "valid": stdout == "VALID", "validation_output": stdout,
                })
            else:
                validated_queries.append({**q, "valid": None, "validation_output": "Not a SELECT"})

        # ── MCP: generate_chart — render recommended charts as base64 PNGs ────
        # DataAgent uses the chart_recommendations from Gemini to produce actual
        # chart images that the Assembler can embed in the final deliverable.
        generated_charts: list[dict] = []
        for rec in result.get("chart_recommendations", [])[:3]:   # cap at 3 charts
            # rec format: "bar: Revenue by region (labels: Q1/Q2/Q3, values: 120/95/140)"
            # Derive chart_type from the recommendation string prefix
            chart_type = "bar"   # safe default
            for ct in ("bar", "line", "pie", "scatter", "histogram"):
                if ct in rec.lower():
                    chart_type = ct
                    break

            # Ask Gemini to generate concrete chart data from the analysis
            chart_data_prompt = (
                f"Based on this analysis:\n{result.get('analysis', '')[:1000]}\n\n"
                f"Generate chart data for: {rec}\n"
                f"Chart type: {chart_type}\n"
                f"Return ONLY valid JSON matching this schema:\n"
                + ('{"labels": ["A","B","C"], "values": [1,2,3]}'
                   if chart_type in ("bar", "line", "pie")
                   else '{"x": [1,2,3], "y": [4,5,6]}'
                   if chart_type == "scatter"
                   else '{"values": [1,2,3,4,5]}')
            )
            try:
                chart_data = await self.gemini.generate_json(
                    "You generate chart data as compact JSON. No explanation.",
                    chart_data_prompt,
                    stream_session_id=session_id,
                    stream_memory=self.memory,
                )
                await self.emit_event(session_id, "TOOL_CALLED", {
                    "task_id": task_id, "tool": "generate_chart", "chart_type": chart_type,
                })
                chart_result = await tool_registry.call(
                    "generate_chart",
                    chart_type=chart_type,
                    data=str(chart_data) if isinstance(chart_data, str) else __import__("json").dumps(chart_data),
                    title=rec[:60],
                )
                if chart_result.get("success"):
                    generated_charts.append({
                        "recommendation": rec,
                        "chart_type":     chart_type,
                        "markdown":       chart_result.get("markdown", ""),
                    })
            except Exception as ce:
                print(f"[DataAgent] chart generation skipped: {ce}")

        output = {
            "task_id":               task_id,
            "agent":                 self.name,
            "analysis":              result.get("analysis", ""),
            "insights":              result.get("insights", []),
            "schema_suggestions":    result.get("schema_suggestions", []),
            "sql_queries":           validated_queries,
            "validated_code":        result.get("validated_code", []),
            "chart_recommendations": result.get("chart_recommendations", []),
            "generated_charts":      generated_charts,
            "tool_calls_made":       len(tool_call_log),
            "summary":               result.get("summary", ""),
        }

        await self.store_output(session_id, task_id, output)

        # ── A2A: respond to any peer requests ─────────────────────────────────
        await self.respond_to_a2a_requests(
            session_id,
            current_output=output,
            system_context=f"Insights: {output['insights'][:3]}",
        )

        await self.emit_event(session_id, "TASK_COMPLETE", {
            "task_id":          task_id,
            "summary":          output["summary"],
            "tool_calls_made":  len(tool_call_log),
            "sql_validated":    len(validated_queries),
            "charts_generated": len(generated_charts),
        })

        return output
