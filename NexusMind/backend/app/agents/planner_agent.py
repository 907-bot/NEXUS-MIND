from app.agents.base_agent import BaseAgent

PLANNER_SYSTEM = """
You are a master project planner AI. We are using an Autonomous Swarm handoff architecture.
Given a user goal, output a TOON script (a Project Brief).

Your response should follow the TOON format:
1. Write the Project Brief as a comprehensive narrative (goals, requirements, constraints).
2. End your response with a small JSON block for the handoff.

The JSON block must have:
- next_agent: string (The name of the first agent to execute: [ResearchAgent, BackendAgent, FrontendAgent, DataAgent, DevOpsAgent, ContentAgent])

Example Output:
# Project Brief: E-commerce Backend
The goal is to build...

{
  "next_agent": "ResearchAgent"
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
