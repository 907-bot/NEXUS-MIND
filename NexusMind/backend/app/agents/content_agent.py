from app.agents.base_agent import BaseAgent

CONTENT_SYSTEM = """
You are a professional content creator and technical writer.
Given a task description, produce high-quality, engaging, and professional content.
Respond ONLY with valid JSON in this exact format:
{
  "content": "Full markdown or text content",
  "summary": "Brief description of the content produced",
  "tags": ["tag1", "tag2"]
}
"""


class ContentAgent(BaseAgent):
    name = "ContentAgent"
    skill_tags = ["content", "writing"]

    async def execute(self, session_id: str, task: dict) -> dict:
        task_id = task.get("task_id", "unknown")
        description = task.get("description", "")

        await self.emit_event(session_id, "TASK_STARTED", {
            "task_id": task_id,
            "agent": self.name,
            "description": description,
        })

        result = await self.gemini.generate_json(
            CONTENT_SYSTEM,
            f"Content task: {description}",
            stream_session_id=session_id,
            stream_memory=self.memory,
        )

        output = {
            "task_id": task_id,
            "agent": self.name,
            "content": result.get("content", ""),
            "summary": result.get("summary", ""),
            "tags": result.get("tags", []),
        }

        await self.store_output(session_id, task_id, output)
        await self.emit_event(session_id, "TASK_COMPLETE", {
            "task_id": task_id,
            "summary": output["summary"],
        })

        return output
