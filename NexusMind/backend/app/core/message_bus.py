import time
import uuid
from app.core.memory_store import memory_store


class MessageBus:
    """
    Agent-to-Agent (A2A) communication layer.
    Messages are published via Redis pub/sub so any subscriber
    (SSE endpoint, other agents) can consume them in real time.
    Uses TOON (Token Oriented Object Notation) for serialization.
    """

    async def send(
        self,
        session_id: str,
        from_agent: str,
        to_agent: str,
        msg_type: str,
        payload: dict,
    ) -> str:
        """Send a directed message between agents using TOON format."""
        message = {
            "message_id": f"msg_{uuid.uuid4().hex[:8]}",
            "from_agent": from_agent,
            "to_agent": to_agent,
            "session_id": session_id,
            "type": msg_type,
            "timestamp": time.time(),
            "payload": payload,
        }
        await memory_store.publish_event(session_id, message)

        # Also persist to memory so agents can read it later
        key = f"a2a:{from_agent}:{to_agent}:{message['message_id']}"
        await memory_store.set(session_id, key, message)
        return message["message_id"]

    async def broadcast(self, session_id: str, from_agent: str, msg_type: str, data: dict):
        """Broadcast a system-wide event (e.g., task status update) using TOON format."""
        event = {
            "message_id": f"msg_{uuid.uuid4().hex[:8]}",
            "from_agent": from_agent,
            "to_agent": "ALL",
            "session_id": session_id,
            "type": msg_type,
            "timestamp": time.time(),
            "payload": data,
        }
        await memory_store.publish_event(session_id, event)


message_bus = MessageBus()
