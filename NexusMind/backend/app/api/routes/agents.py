from fastapi import APIRouter, Depends
from app.core.agent_registry import agent_registry
from app.api.middleware import get_current_user

router = APIRouter(prefix="/api/agents", tags=["agents"])

@router.get("")
async def list_agents(user=Depends(get_current_user)):
    """List all registered agents and their capabilities."""
    return {"agents": agent_registry.get_all()}

@router.get("/{agent_id}/status")
async def get_agent_status(agent_id: str, user=Depends(get_current_user)):
    """Get the current status of a specific agent."""
    agents = agent_registry.get_all()
    agent = next((a for a in agents if a["agent_id"] == agent_id), None)
    return agent if agent else {"error": "Agent not found"}
