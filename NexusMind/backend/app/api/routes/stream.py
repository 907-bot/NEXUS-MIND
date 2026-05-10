from fastapi import APIRouter, Request, Depends
from sse_starlette.sse import EventSourceResponse
from app.core.memory_store import memory_store
from app.api.middleware import get_current_user_ws
import asyncio
import json

router = APIRouter(prefix="/api/stream", tags=["stream"])

# Maximum time (seconds) to wait for a new event before sending a keep-alive ping.
KEEPALIVE_INTERVAL = 15


@router.get("/{session_id}")
async def stream_session(
    session_id: str,
    request: Request,
    # BUG FIX: browsers cannot set headers on native EventSource, so we read
    # the Clerk JWT from the `?token=` query param instead of the Auth header.
    # CRITICAL FIX: must use Depends() — without it FastAPI passes the function
    # object itself and auth is never executed (security hole).
    user=Depends(get_current_user_ws),
):
    """
    Stream agent events for a session using Server-Sent Events (SSE).
    Connect via: EventSource(`/api/stream/{session_id}?token=<jwt>`)
    """
    async def event_generator():
        pubsub = await memory_store.subscribe(session_id)
        try:
            # Initial handshake event
            yield {
                "event": "message",
                "data": json.dumps({
                    "agent": "System",
                    "type": "CONNECTED",
                    "data": {"session_id": session_id},
                }),
            }

            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                # Non-blocking check for the next Redis pub/sub message
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=KEEPALIVE_INTERVAL
                )

                if message and message.get("type") == "message":
                    yield {"event": "message", "data": message["data"]}

                    # Close stream gracefully after final output
                    try:
                        parsed = json.loads(message["data"])
                        if parsed.get("type") in ("FINAL_OUTPUT", "PIPELINE_ERROR"):
                            break
                    except (json.JSONDecodeError, AttributeError):
                        pass
                else:
                    # Send a keep-alive comment to prevent proxy timeout
                    yield {"event": "ping", "data": ""}

                await asyncio.sleep(0.05)
        finally:
            await pubsub.unsubscribe()

    return EventSourceResponse(event_generator())
