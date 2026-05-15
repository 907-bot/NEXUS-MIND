from app.agents.base_agent import BaseAgent

PLANNER_SYSTEM = """
You are a master project planner AI. We are using an Autonomous Swarm handoff architecture.

ROUTING LOGIC:
1. **Application Creation**: If the user wants to build/create an app, route to [ResearchAgent, BackendAgent, or FrontendAgent].
2. **Knowledge Retrieval**: If the user is asking a simple question or looking for a definition (e.g., "What is ML?", "How does DL work?"), route DIRECTLY to the [ContentAgent].

Your response should follow the TOON format:
1. Write the Project Brief or Query Summary as a comprehensive narrative.
2. End your response with a small JSON block for the handoff.

The JSON block must have:
- next_agent: string (The name of the first agent to execute)

Example Output (Knowledge Query):
# Deep Learning Explained
The user wants to understand the core concepts of Deep Learning...

{
  "next_agent": "ContentAgent"
}
"""


class PlannerAgent(BaseAgent):
    name = "PlannerAgent"
    skill_tags = ["planning"]

    async def execute(self, session_id: str, task: dict) -> dict:
        goal = task.get("goal", "")
        await self.emit_event(session_id, "PLANNING_STARTED", {"goal": goal})

        try:
            plan_data = await self.gemini.generate_json(
                PLANNER_SYSTEM,
                f"Goal: {goal}",
                stream_session_id=session_id,
                stream_memory=self.memory,
            )
        except Exception as e:
            print(f"⚠️ [PlannerAgent] Plan generation failed: {e}. Using fallback plan.")
            plan_data = {
                "brief": f"Fallback Project Plan for: {goal}. Auto-generated due to rate limits.",
                "next_agent": "ResearchAgent"
            }

        # Validate structure - TOON narrative is the brief
        brief = plan_data.get("_toon_narrative", plan_data.get("brief", "No brief provided."))
        next_agent = plan_data.get("next_agent", "ResearchAgent")

        await self.memory.set(session_id, "project_brief", brief)
        
        # BOLD LOG for Render Console debugging
        print("\n" + "="*50)
        print(f"📝 [PLANNER] GENERATED TOON SCRIPT FOR SESSION {session_id}")
        print(f"  - Brief: {brief[:100]}...")
        print(f"  - Next Agent: {next_agent}")
        print("="*50 + "\n")

        await self.emit_event(
            session_id,
            "PLANNING_COMPLETE",
            {"brief": brief, "next_agent": next_agent},
        )

        return {"brief": brief, "next_agent": next_agent}
