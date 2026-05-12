from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AgentInfo:
    agent_id: str
    name: str
    skill_tags: List[str]
    status: str = "idle"          # idle | busy | error
    max_concurrent_tasks: int = 3
    avg_completion_time_ms: int = 5000
    success_rate: float = 0.95
    active_tasks: int = 0


class AgentRegistry:
    """
    In-memory registry of all available agents.
    Used by the Orchestrator to discover and select agents by skill tag.
    """

    def __init__(self):
        self._agents: Dict[str, AgentInfo] = {}

    def register(self, agent: AgentInfo):
        self._agents[agent.agent_id] = agent

    def get_by_skill(self, skill_tag: str) -> Optional[AgentInfo]:
        """Return the best-fit idle agent for a given skill tag."""
        candidates = [
            a for a in self._agents.values()
            if skill_tag in a.skill_tags and a.active_tasks < a.max_concurrent_tasks
        ]
        if not candidates:
            return None
        # Pick highest success rate
        return max(candidates, key=lambda a: a.success_rate)

    def get_all(self) -> List[Dict]:
        return [
            {
                "agent_id": a.agent_id,
                "name": a.name,
                "skill_tags": a.skill_tags,
                "status": a.status,
                "max_concurrent_tasks": a.max_concurrent_tasks,
                "avg_completion_time_ms": a.avg_completion_time_ms,
                "success_rate": a.success_rate,
            }
            for a in self._agents.values()
        ]

    def mark_busy(self, agent_id: str):
        if agent_id in self._agents:
            self._agents[agent_id].active_tasks += 1
            self._agents[agent_id].status = "busy"

    def mark_idle(self, agent_id: str):
        if agent_id in self._agents:
            a = self._agents[agent_id]
            a.active_tasks = max(0, a.active_tasks - 1)
            if a.active_tasks == 0:
                a.status = "idle"


# Singleton populated at app startup
agent_registry = AgentRegistry()


def bootstrap_registry():
    """Register all built-in agents into the registry."""
    agents = [
        AgentInfo("planner_v1",    "Planner Agent",    ["planning"],                    max_concurrent_tasks=1),
        AgentInfo("backend_v1",    "Backend Agent",    ["backend", "database", "api"],  max_concurrent_tasks=3),
        AgentInfo("frontend_v1",   "Frontend Agent",   ["frontend", "ui"],              max_concurrent_tasks=3),
        AgentInfo("research_v1",   "Research Agent",   ["research"],                    max_concurrent_tasks=2),
        AgentInfo("data_v1",       "Data Agent",       ["data", "analytics"],           max_concurrent_tasks=2),
        AgentInfo("content_v1",    "Content Agent",    ["content", "writing"],          max_concurrent_tasks=3),
        AgentInfo("devops_v1",     "DevOps Agent",     ["devops", "infra"],             max_concurrent_tasks=2),
        AgentInfo("critic_v1",     "Critic Agent",     ["review", "critic"],            max_concurrent_tasks=1),
        AgentInfo("assembler_v1",  "Assembler Agent",  ["assembly"],                    max_concurrent_tasks=1),
    ]
    for a in agents:
        agent_registry.register(a)
        print(f"📦 [REGISTRY] Agent '{a.name}' ({a.agent_id}) registered with skills: {a.skill_tags}")
