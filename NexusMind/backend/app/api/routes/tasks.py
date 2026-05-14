from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from app.agents.planner_agent import PlannerAgent
from app.agents.orchestrator import Orchestrator
from app.core.gemini_client import gemini
from app.core.memory_store import memory_store
from app.api.middleware import get_current_user
from app.database import AsyncSessionLocal
from app.models.session import Session
from app.models.task import Task
import uuid
import time
from collections import defaultdict
from typing import Dict, List

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# ── In-memory rate limiter: max 10 goal submissions per user per hour ─────────
_rate_limit_store: Dict[str, List[float]] = defaultdict(list)
RATE_LIMIT_MAX = 10
RATE_LIMIT_WINDOW = 3600  # seconds


def _check_rate_limit(user_id: str) -> bool:
    """Return True if within rate limit, False if exceeded."""
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    calls = _rate_limit_store[user_id]
    _rate_limit_store[user_id] = [t for t in calls if t > window_start]
    if len(_rate_limit_store[user_id]) >= RATE_LIMIT_MAX:
        return False
    _rate_limit_store[user_id].append(now)
    return True


class GoalRequest(BaseModel):
    goal: str


async def run_nexusmind_pipeline(session_id: str, goal: str, user_id: str):
    """Background task: plan → orchestrate → persist results to PostgreSQL."""
    try:
        # Grace period to allow frontend SSE stream to connect before events are published
        await asyncio.sleep(1.5)
        await memory_store.set_status(session_id, "planning")

        # Persist session to PostgreSQL
        async with AsyncSessionLocal() as db:
            db_session = Session(id=session_id, user_id=user_id, goal=goal, status="planning")
            db.add(db_session)
            await db.commit()

        # Step 1: Decompose Goal into Task Graph (Planner uses native Gemini)
        planner = PlannerAgent(gemini, memory_store, use_openrouter=True)
        print(f"🎯 [PIPELINE] PlannerAgent initialized for session {session_id}")
        await memory_store.publish_event(
            session_id,
            {
                "agent": "System",
                "type": "BACKEND_LOG",
                "timestamp": time.time(),
                "data": {
                    "message": "Starting **PlannerAgent** — goal decomposition in progress.",
                    "phase": "pipeline_started",
                },
            },
        )
        result = await planner.execute(session_id, {"goal": goal})
        brief = result.get("brief")
        next_agent = result.get("next_agent")

        if not brief:
            await memory_store.publish_event(session_id, {
                "agent": "System",
                "type": "ERROR",
                "data": {"message": "Failed to generate project brief."},
            })
            await memory_store.set_status(session_id, "failed")
            async with AsyncSessionLocal() as db:
                db_sess = await db.get(Session, session_id)
                if db_sess:
                    db_sess.status = "failed"
                    await db.commit()
            return

        # Step 2: Execute Autonomous Swarm via Orchestrator
        await memory_store.set_status(session_id, "executing")
        orchestrator = Orchestrator(gemini, memory_store, use_openrouter=True)
        print(f"🎭 [PIPELINE] Orchestrator initialized for session {session_id}")
        await orchestrator.run(session_id, {"brief": brief, "starting_agent": next_agent})

        await memory_store.set_status(session_id, "completed")
        async with AsyncSessionLocal() as db:
            db_sess = await db.get(Session, session_id)
            if db_sess:
                db_sess.status = "completed"
            await db.commit()

    except Exception as e:
        print(f"❌ [PIPELINE ERROR] Session {session_id} failed: {e}")
        import traceback
        traceback.print_exc()
        await memory_store.set_status(session_id, "failed")
        await memory_store.publish_event(session_id, {
            "agent": "System",
            "type": "PIPELINE_ERROR",
            "data": {"error": str(e)},
        })
        async with AsyncSessionLocal() as db:
            db_sess = await db.get(Session, session_id)
            if db_sess:
                db_sess.status = "failed"
            await db.commit()


@router.post("/submit")
async def submit_goal(
    request: GoalRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
):
    """Submit a new goal for multi-agent processing."""
    user_id = user["user_id"]

    # Rate limiting: 10 submissions per user per hour
    if not _check_rate_limit(user_id):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: max {RATE_LIMIT_MAX} submissions per hour.",
        )

    session_id = str(uuid.uuid4())
    await memory_store.set_status(session_id, "initialized")

    background_tasks.add_task(run_nexusmind_pipeline, session_id, request.goal, user_id)

    return {
        "session_id": session_id,
        "status": "processing",
        "user_id": user_id,
        "estimated_completion_ms": 30_000,
    }
