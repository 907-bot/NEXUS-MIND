from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
import asyncio


@dataclass
class TaskNode:
    task_id: str
    description: str
    skill_tag: str
    depends_on: List[str] = field(default_factory=list)
    priority: int = 2
    status: str = "pending"   # pending | running | done | failed
    output: Optional[dict] = None


class TaskGraph:
    """
    Directed Acyclic Graph (DAG) of tasks.
    Provides topological-sort-based ready-task resolution.
    """

    def __init__(self, tasks: List[dict]):
        self.nodes: Dict[str, TaskNode] = {}
        for t in tasks:
            self.nodes[t["task_id"]] = TaskNode(
                task_id=t["task_id"],
                description=t["description"],
                skill_tag=t.get("skill_tag", "content"),
                depends_on=t.get("depends_on", []),
                priority=t.get("priority", 2),
            )
            
        # Clean invalid dependencies that don't exist in the graph
        valid_ids = set(self.nodes.keys())
        for node in self.nodes.values():
            node.depends_on = [dep for dep in node.depends_on if dep in valid_ids]

    def get_ready(self) -> List[TaskNode]:
        """Return all pending tasks whose dependencies are completed."""
        completed_ids: Set[str] = {
            tid for tid, node in self.nodes.items() if node.status == "done"
        }
        ready = [
            node
            for node in self.nodes.values()
            if node.status == "pending"
            and all(dep in completed_ids for dep in node.depends_on)
        ]
        # Sort by priority (lower number = higher priority)
        return sorted(ready, key=lambda n: n.priority)

    def mark_running(self, task_id: str):
        self.nodes[task_id].status = "running"

    def mark_done(self, task_id: str, output: dict):
        self.nodes[task_id].status = "done"
        self.nodes[task_id].output = output

    def mark_failed(self, task_id: str):
        self.nodes[task_id].status = "failed"

    def is_complete(self) -> bool:
        return all(n.status in ("done", "failed") for n in self.nodes.values())

    def has_stuck(self) -> bool:
        """Detect circular dependencies or all-blocked state."""
        # If any task is running, we are not stuck yet, it might finish and unblock others
        if any(n.status == "running" for n in self.nodes.values()):
            return False
        
        pending = [n for n in self.nodes.values() if n.status == "pending"]
        if not pending:
            return False
            
        # If we have pending tasks, no running tasks, and no ready tasks, we are stuck
        return len(self.get_ready()) == 0

    def summary(self) -> dict:
        statuses = {}
        for n in self.nodes.values():
            statuses.setdefault(n.status, 0)
            statuses[n.status] += 1
        return statuses
