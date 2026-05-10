from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from app.core.memory_store import memory_store
from app.api.middleware import get_current_user
from app.database import AsyncSessionLocal
from app.models.session import Session

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


# ── Helper: enforce session ownership ────────────────────────────────────────

async def _get_owned_session(session_id: str, user_id: str) -> Session:
    """
    Load a Session from PostgreSQL and verify it belongs to user_id.
    Raises 404 if not found, 403 if owned by a different user.
    This enforces the SKILL.md security model:
      'Users can only access their own sessions (user_id checked in routes)'
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Session).where(Session.id == session_id)
        )
        session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != user_id:
        # Return 404 rather than 403 to avoid leaking existence of other users' sessions
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("")
async def list_sessions(user=Depends(get_current_user)):
    """List all sessions for the authenticated user (from PostgreSQL)."""
    user_id = user["user_id"]
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Session)
            .where(Session.user_id == user_id)
            .order_by(Session.created_at.desc())
            .limit(50)
        )
        sessions = result.scalars().all()
    return {
        "sessions": [
            {
                "session_id": s.id,
                "goal": s.goal,
                "status": s.status,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in sessions
        ]
    }


@router.get("/{session_id}/status")
async def get_session_status(session_id: str, user=Depends(get_current_user)):
    """Get the high-level execution status of a session."""
    await _get_owned_session(session_id, user["user_id"])  # ownership check
    status = await memory_store.get_status(session_id)
    if not status:
        # Session exists in DB but Redis data expired — check DB status
        async with AsyncSessionLocal() as db:
            s = await db.get(Session, session_id)
            status = s.status if s else "unknown"
    return {"session_id": session_id, "status": status}


@router.get("/{session_id}/output")
async def get_session_output(session_id: str, user=Depends(get_current_user)):
    """Get the final assembled deliverable for a session."""
    await _get_owned_session(session_id, user["user_id"])  # ownership check
    output = await memory_store.get(session_id, "final_output")
    if not output:
        status = await memory_store.get_status(session_id)
        raise HTTPException(
            status_code=202,
            detail=f"Output not yet available — session status: {status or 'unknown'}",
        )
    return output


@router.get("/{session_id}/memory")
async def get_session_memory(session_id: str, user=Depends(get_current_user)):
    """Return the full shared memory state for a session (debugging / dev use)."""
    await _get_owned_session(session_id, user["user_id"])  # ownership check
    memory = await memory_store.get_all(session_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Session memory empty or expired")
    return memory


@router.delete("/{session_id}")
async def delete_session(session_id: str, user=Depends(get_current_user)):
    """
    Delete Redis session data.
    PostgreSQL audit records are retained per the 30-day retention policy.
    """
    await _get_owned_session(session_id, user["user_id"])  # ownership check
    await memory_store.delete_session(session_id)
    return {"session_id": session_id, "deleted": True}
