from app.agents.base_agent import BaseAgent

PLANNER_SYSTEM = """
You are a master project planner AI. Given a user goal, decompose it into atomic subtasks.
Output ONLY a JSON array. Each task object must have exactly these fields:
- task_id: unique string (e.g. "task_001")
- description: clear, actionable instruction for the executing agent
- skill_tag: exactly one of [backend, frontend, research, data, content, devops, review]
- depends_on: list of task_ids this task must wait for (empty list if none)
- priority: integer 1 (high) to 3 (low)

Rules:
- Decompose into 3-10 atomic tasks. Do not create overly granular tasks.
- Ensure the final task has skill_tag "review" and depends on all other tasks.
- Do NOT include any text outside the JSON array.
"""


class PlannerAgent(BaseAgent):
    name = "PlannerAgent"
    skill_tags = ["planning"]

    async def execute(self, session_id: str, task: dict) -> dict:
        goal = task.get("goal", "")
        await self.emit_event(session_id, "PLANNING_STARTED", {"goal": goal})

        task_graph = await self.gemini.generate_json(
            PLANNER_SYSTEM, f"Goal: {goal}"
        )

        # Validate it's a list
        if not isinstance(task_graph, list):
            task_graph = task_graph.get("tasks", [])

        await self.memory.set(session_id, "task_graph", task_graph)
        
        # BOLD LOG for Render Console debugging
        print("\n" + "="*50)
        print(f"📝 [PLANNER] GENERATED {len(task_graph)} TASKS FOR SESSION {session_id}")
        for t in task_graph:
            print(f"  - [{t.get('skill_tag')}] {t.get('task_id')}: {t.get('description')}")
        print("="*50 + "\n")

        await self.emit_event(
            session_id,
            "PLANNING_COMPLETE",
            {"task_count": len(task_graph), "tasks": task_graph},
        )

        return {"task_graph": task_graph}
