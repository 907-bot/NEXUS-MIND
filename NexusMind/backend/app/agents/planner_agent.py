from app.agents.base_agent import BaseAgent

PLANNER_SYSTEM = """
You are a master project planner AI. We are using an Autonomous Swarm handoff architecture.
Given a user goal, output a TOON script (a Project Brief).
Output ONLY a JSON object. Do NOT include any markdown formatting, preamble, or postscript.

The JSON object must have exactly these fields:
- brief: string (A comprehensive summary of the project goals, requirements, and constraints)
- next_agent: string (The name of the first agent to execute. Choose from: [ResearchAgent, BackendAgent, FrontendAgent, DataAgent, DevOpsAgent, ContentAgent])

Example:
{"brief": "Build a React frontend and FastAPI backend for...", "next_agent": "ResearchAgent"}
"""


class PlannerAgent(BaseAgent):
    name = "PlannerAgent"
    skill_tags = ["planning"]

    async def execute(self, session_id: str, task: dict) -> dict:
        goal = task.get("goal", "")
        await self.emit_event(session_id, "PLANNING_STARTED", {"goal": goal})

        plan_data = await self.gemini.generate_json(
            PLANNER_SYSTEM,
            f"Goal: {goal}",
            stream_session_id=session_id,
            stream_memory=self.memory,
        )

        # Validate structure
        brief = plan_data.get("brief", "No brief provided.")
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
