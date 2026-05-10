from app.agents.base_agent import BaseAgent

CRITIC_SYSTEM = """
You are a strict quality assurance reviewer and critic.
Review the provided task outputs and identify any issues, missing parts, or bugs.
Respond ONLY with valid JSON in this exact format:
{
  "score": 85,
  "issues": [
    {"task_id": "t001", "issue": "Missing field in schema", "severity": "high"}
  ],
  "approved": true,
  "feedback": "Overall good, but needs minor fixes."
}
"""


class CriticAgent(BaseAgent):
    name = "CriticAgent"
    skill_tags = ["review", "critic"]

    async def execute(self, session_id: str, task: dict) -> dict:
        outputs = task.get("outputs", {})
        await self.emit_event(session_id, "REVIEW_STARTED", {"outputs_count": len(outputs)})

        result = await self.gemini.generate_json(
            CRITIC_SYSTEM,
            f"Review these agent outputs: {outputs}"
        )

        output = {
            "score": result.get("score", 0),
            "issues": result.get("issues", []),
            "approved": result.get("approved", False),
            "feedback": result.get("feedback", ""),
        }

        await self.memory.set(session_id, "critic_review", output)
        await self.emit_event(session_id, "REVIEW_COMPLETE", output)

        return output
