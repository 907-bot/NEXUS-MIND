from abc import ABC, abstractmethod
from app.core.gemini_client import GeminiClient
from app.core.memory_store import MemoryStore
from app.core.message_bus import message_bus
import time


class BaseAgent(ABC):
    """
    Abstract base for all NexusMind agents.

    Provides:
      - emit_event()               → broadcast an event to the SSE stream (A2A bus)
      - send_a2a_message()         → send a directed INFORMATION_REQUEST to another agent
      - respond_to_a2a_requests()  → read pending requests directed at this agent,
                                     generate answers, send INFORMATION_RESPONSE back
      - read_a2a_responses()       → read INFORMATION_RESPONSE messages sent to this agent
      - store_output()             → persist task output to shared Redis memory
      - read_context()             → read another agent's output from shared memory
    """
    name: str = "BaseAgent"
    skill_tags: list[str] = []

    def __init__(self, gemini: GeminiClient, memory: MemoryStore):
        self.gemini = gemini
        self.memory = memory

    @abstractmethod
    async def execute(self, session_id: str, task: dict) -> dict:
        """Execute a task and return an output dict."""
        pass

    # ── A2A: Broadcast event ──────────────────────────────────────────────────

    async def emit_event(self, session_id: str, event_type: str, data: dict):
        """
        Publish an event to the A2A message bus / SSE stream.
        All connected clients and subscribing agents receive it.
        """
        event = {
            "agent": self.name,
            "type": event_type,
            "timestamp": time.time(),
            "data": data,
        }
        await self.memory.publish_event(session_id, event)
        print(f"[{self.name}] {event_type}: {data}")

    # ── A2A: Send directed request ────────────────────────────────────────────

    async def send_a2a_message(
        self,
        session_id: str,
        to_agent: str,
        msg_type: str,
        payload: dict,
    ) -> str:
        """
        Send a directed A2A message to a specific agent.

        The message is persisted in shared memory so the target agent can read
        it via read_a2a_messages() at any point during execution.

        msg_type should be one of:
          - INFORMATION_REQUEST  → asking the target for specific data
          - INFORMATION_RESPONSE → replying to a prior request
          - CONTEXT_NOTIFY       → informational broadcast (no reply expected)

        Returns:
            message_id: the unique ID of the sent message.
        """
        msg_id = await message_bus.send(
            session_id=session_id,
            from_agent=self.name,
            to_agent=to_agent,
            msg_type=msg_type,
            payload=payload,
        )
        await self.emit_event(session_id, "A2A_MESSAGE_SENT", {
            "from": self.name,
            "to": to_agent,
            "type": msg_type,
            "message_id": msg_id,
        })
        return msg_id

    # ── A2A: Read all incoming messages ───────────────────────────────────────

    async def read_a2a_messages(self, session_id: str) -> list[dict]:
        """Read all A2A messages directed at this agent from shared memory."""
        all_memory = await self.memory.get_all(session_id)
        messages = []
        for key, value in all_memory.items():
            if isinstance(value, dict) and value.get("to_agent") == self.name:
                messages.append(value)
        return messages

    # ── A2A: Respond to pending INFORMATION_REQUEST messages ──────────────────

    async def respond_to_a2a_requests(
        self,
        session_id: str,
        current_output: dict,
        system_context: str = "",
    ) -> list[str]:
        """
        Read all pending INFORMATION_REQUEST messages directed at this agent,
        use Gemini to generate a focused answer for each, then send
        INFORMATION_RESPONSE messages back to the requesting agents.

        Args:
            session_id:      Current session.
            current_output:  This agent's freshly-produced output dict.
            system_context:  Extra context string to help Gemini answer.

        Returns:
            List of message_ids of the responses sent.
        """
        messages = await self.read_a2a_messages(session_id)
        requests = [m for m in messages if m.get("type") == "INFORMATION_REQUEST"]
        response_ids = []

        for req in requests:
            from_agent = req.get("from_agent", "Unknown")
            request_text = req.get("payload", {}).get("request", "")
            req_msg_id = req.get("message_id", "")

            if not request_text:
                continue

            # Use Gemini to generate a targeted answer based on this agent's output
            answer_prompt = (
                f"You are {self.name}. Another agent ({from_agent}) is asking:\n"
                f'"{request_text}"\n\n'
                f"Your current task output:\n{current_output}\n\n"
                f"{system_context}\n\n"
                "Provide a concise, precise answer. Focus only on what was asked."
            )
            answer = await self.gemini.generate(
                "You are an expert AI agent responding to a peer agent's request. "
                "Be concise and technically accurate.",
                answer_prompt,
            )

            resp_id = await message_bus.send(
                session_id=session_id,
                from_agent=self.name,
                to_agent=from_agent,
                msg_type="INFORMATION_RESPONSE",
                payload={
                    "reply_to_message_id": req_msg_id,
                    "request": request_text,
                    "response": answer,
                },
            )
            await self.emit_event(session_id, "A2A_RESPONSE_SENT", {
                "from": self.name,
                "to": from_agent,
                "reply_to": req_msg_id,
                "message_id": resp_id,
            })
            response_ids.append(resp_id)

        return response_ids

    # ── A2A: Read INFORMATION_RESPONSE messages addressed to this agent ───────

    async def read_a2a_responses(self, session_id: str) -> list[dict]:
        """
        Read all INFORMATION_RESPONSE messages that other agents have sent
        back to this agent (i.e., replies to prior INFORMATION_REQUESTs).
        """
        all_memory = await self.memory.get_all(session_id)
        responses = []
        for key, value in all_memory.items():
            if (
                isinstance(value, dict)
                and value.get("type") == "INFORMATION_RESPONSE"
                and value.get("to_agent") == self.name
            ):
                responses.append(value)
        return responses

    # ── Shared memory helpers ─────────────────────────────────────────────────

    async def store_output(self, session_id: str, task_id: str, output: dict):
        """Persist task output to shared memory (accessible by other agents)."""
        await self.memory.set(session_id, f"output:{task_id}", output)

    async def read_context(self, session_id: str, task_id: str) -> dict | None:
        """Read another agent's output from shared memory by task_id."""
        return await self.memory.get(session_id, f"output:{task_id}")
