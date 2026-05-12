import asyncio
from typing import Dict, List
from app.core.gemini_client import GeminiClient
from app.core.memory_store import MemoryStore
from app.core.task_graph import TaskGraph, TaskNode
from app.core.agent_registry import agent_registry
from app.agents.backend_agent import BackendAgent
from app.agents.frontend_agent import FrontendAgent
from app.agents.research_agent import ResearchAgent
from app.agents.data_agent import DataAgent
from app.agents.content_agent import ContentAgent
from app.agents.devops_agent import DevOpsAgent
from app.agents.critic_agent import CriticAgent
from app.agents.assembler_agent import AssemblerAgent
from app.database import AsyncSessionLocal
from app.models.agent_output import AgentOutput
import uuid

SKILL_TO_AGENT = {
    "backend":  BackendAgent,
    "frontend": FrontendAgent,
    "research": ResearchAgent,
    "data":     DataAgent,
    "content":  ContentAgent,
    "devops":   DevOpsAgent,
    "review":   CriticAgent,
}

# Maps AgentClass → registry agent_id for mark_busy/mark_idle
AGENT_REGISTRY_ID = {
    BackendAgent:   "backend_v1",
    FrontendAgent:  "frontend_v1",
    ResearchAgent:  "research_v1",
    DataAgent:      "data_v1",
    ContentAgent:   "content_v1",
    DevOpsAgent:    "devops_v1",
    CriticAgent:    "critic_v1",
    AssemblerAgent: "assembler_v1",
}


class Orchestrator:
    def __init__(self, gemini: GeminiClient, memory: MemoryStore, use_openrouter: bool = True):
        self.gemini = gemini
        self.memory = memory
        self.use_openrouter = use_openrouter
        print(f"🎭 [Orchestrator] Initialized (OpenRouter: {'✅ Enabled' if use_openrouter else '❌ Disabled'})")

    async def run(self, session_id: str, task_list: List[dict]):
        """
        Execute the task graph respecting dependencies, with full parallel
        dispatch of independent tasks.
        """
        graph = TaskGraph(task_list)
        completed: Dict[str, dict] = {}
        
        # Start background ETA logger
        stop_event = asyncio.Event()
        eta_task = asyncio.create_task(self._log_eta_periodically(session_id, graph, stop_event))

        try:
            while not graph.is_complete():
                ready_tasks = graph.get_ready()

                if not ready_tasks:
                    if graph.has_stuck():
                        await self.memory.publish_event(session_id, {
                            "agent": "Orchestrator",
                            "type": "ERROR",
                            "data": {"message": "Execution stuck — circular dependency or all tasks failed."},
                        })
                        break
                    await asyncio.sleep(0.5)
                    continue

                await asyncio.gather(*(
                    self._execute_task(session_id, node, graph, completed)
                    for node in ready_tasks
                ))

            # ── Post-execution: Critic → revision loop → Assembler ────────────────
            if graph.is_complete():
                all_outputs = await self.memory.get_all(session_id)
                review_result = {}

                MAX_REVISION_CYCLES = 2
                for cycle in range(MAX_REVISION_CYCLES):
                    critic = CriticAgent(self.gemini, self.memory, use_openrouter=self.use_openrouter)
                    print(f"🕵️ [ORCHESTRATOR] Agent 'CriticAgent' initialized/started for cycle {cycle}")
                    review_result = await critic.execute(session_id, {"outputs": all_outputs})

                    # ── Audit: store Critic output ─────────────────────────────────
                    await self._write_audit(
                        session_id=session_id,
                        task_id=f"critic_cycle_{cycle}",
                        agent_name="CriticAgent",
                        skill_tag="review",
                        output=review_result,
                        quality_score=review_result.get("score"),
                    )

                    if review_result.get("approved", True):
                        break

                    high_issues = [
                        i for i in review_result.get("issues", [])
                        if i.get("severity") == "high"
                    ]
                    if not high_issues:
                        break

                    await self.memory.publish_event(session_id, {
                        "agent": "Orchestrator",
                        "type": "REVISION_STARTED",
                        "data": {"cycle": cycle + 1, "high_issues": len(high_issues)},
                    })

                    correction_tasks = [
                        {
                            "task_id": f"correction_{issue['task_id']}_c{cycle}",
                            "description": (
                                f"Correction for {issue['task_id']}: {issue['issue']}"
                            ),
                            "skill_tag": self._skill_for_task(issue["task_id"], graph),
                            "depends_on": [],
                            "priority": 1,
                        }
                        for issue in high_issues
                    ]
                    correction_graph = TaskGraph(correction_tasks)
                    completed_corrections: dict = {}
                    while not correction_graph.is_complete():
                        ready = correction_graph.get_ready()
                        if not ready:
                            break
                        await asyncio.gather(*(
                            self._execute_task(session_id, node, correction_graph, completed_corrections)
                            for node in ready
                        ))
                    all_outputs = await self.memory.get_all(session_id)

                # ── Final Assembly ─────────────────────────────────────────────────
                assembler = AssemblerAgent(self.gemini, self.memory, use_openrouter=self.use_openrouter)
                print(f"🏗️ [ORCHESTRATOR] Agent 'AssemblerAgent' initialized/started for final assembly")
                # Mark assembler busy in registry
                agent_registry.mark_busy(AGENT_REGISTRY_ID[AssemblerAgent])
                try:
                    asm_result = await assembler.execute(
                        session_id,
                        {"outputs": all_outputs, "review": review_result},
                    )
                    await self._write_audit(
                        session_id=session_id,
                        task_id="assembly",
                        agent_name="AssemblerAgent",
                        skill_tag="assembly",
                        output=asm_result,
                    )
                finally:
                    agent_registry.mark_idle(AGENT_REGISTRY_ID[AssemblerAgent])
        finally:
            stop_event.set()
            await eta_task

    # ── Task execution ────────────────────────────────────────────────────────

    async def _execute_task(
        self,
        session_id: str,
        node: TaskNode,
        graph: TaskGraph,
        completed: dict,
    ):
        AgentClass = SKILL_TO_AGENT.get(node.skill_tag, ContentAgent)
        agent_name = AgentClass.__name__
        registry_id = AGENT_REGISTRY_ID.get(AgentClass, "")

        graph.mark_running(node.task_id)

        # ── #4 FIX: mark agent busy in registry ───────────────────────────────
        if registry_id:
            agent_registry.mark_busy(registry_id)

        await self.memory.publish_event(session_id, {
            "agent": agent_name,
            "type": "TASK_STARTED",
            "data": {
                "task_id": node.task_id,
                "description": node.description,
                "skill_tag": node.skill_tag,
            },
        })

        try:
            agent = AgentClass(self.gemini, self.memory, use_openrouter=self.use_openrouter)
            print(f"🤖 [AGENT] {agent_name} STARTING: {node.task_id}")
            result = await agent.execute(session_id, {
                "task_id": node.task_id,
                "description": node.description,
                "skill_tag": node.skill_tag,
                "context": completed,
            })
            
            # BOLD LOG for Render Console debugging
            print("\n" + "-"*30)
            print(f"✅ [AGENT] {agent_name} COMPLETED: {node.task_id}")
            print(f"📄 RESPONSE: {str(result.get('summary', ''))[:200]}...")
            print("-"*30 + "\n")
            
            graph.mark_done(node.task_id, result)
            completed[node.task_id] = result

            # ── #3 FIX: write AgentOutput audit record to PostgreSQL ───────────
            await self._write_audit(
                session_id=session_id,
                task_id=node.task_id,
                agent_name=agent_name,
                skill_tag=node.skill_tag,
                output=result,
            )

            await self.memory.publish_event(session_id, {
                "agent": agent_name,
                "type": "TASK_COMPLETE",
                "data": {
                    "task_id": node.task_id,
                    "summary": result.get("summary", ""),
                },
            })

        except Exception as exc:
            graph.mark_failed(node.task_id)
            await self.memory.publish_event(session_id, {
                "agent": agent_name,
                "type": "TASK_FAILED",
                "data": {"task_id": node.task_id, "error": str(exc)},
            })
        finally:
            # Always return agent to idle — even on failure
            if registry_id:
                agent_registry.mark_idle(registry_id)

    async def _log_eta_periodically(self, session_id: str, graph: TaskGraph, stop_event: asyncio.Event):
        """Logs the expected time of completion every 2 minutes."""
        interval = 120  # 2 minutes
        while not stop_event.is_set():
            try:
                # Simple heuristic for ETA: remaining tasks * avg time (e.g. 30s per task)
                remaining_tasks = [t for t in graph.nodes.values() if t.status not in ["done", "failed"]]
                # Assume an average of 60 seconds per remaining task for better estimation
                eta_minutes = len(remaining_tasks) * 1.0 
                
                print(f"⏳ [MONITOR] Session {session_id}: {len(remaining_tasks)} tasks remaining. Estimated time to completion: {eta_minutes:.1f} minutes.")
                
                # Wait for interval or stop event
                await asyncio.wait([asyncio.create_task(asyncio.sleep(interval))], return_when=asyncio.FIRST_COMPLETED)
            except Exception as e:
                print(f"⚠️ [MONITOR] Error in ETA logger: {e}")
                break
            
            if stop_event.is_set():
                break

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def _write_audit(
        self,
        session_id: str,
        task_id: str,
        agent_name: str,
        skill_tag: str,
        output: dict,
        quality_score: float | None = None,
    ):
        """Persist an AgentOutput record to PostgreSQL for the 30-day audit log."""
        try:
            async with AsyncSessionLocal() as db:
                record = AgentOutput(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    task_id=task_id,
                    agent_name=agent_name,
                    skill_tag=skill_tag,
                    output=output,
                    quality_score=quality_score,
                )
                db.add(record)
                await db.commit()
        except Exception as e:
            # Audit logging must never crash the pipeline
            print(f"[Orchestrator] audit write failed for {task_id}: {e}")

    def _skill_for_task(self, task_id: str, graph: TaskGraph) -> str:
        node = graph.nodes.get(task_id)
        return node.skill_tag if node else "content"
