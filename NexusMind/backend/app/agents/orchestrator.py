import asyncio
from typing import Dict, List
from app.core.gemini_client import GeminiClient
from app.core.memory_store import MemoryStore
from app.core.openrouter_client import OpenRouterClient
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
import time
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
        print(f"🎭 [Orchestrator] Initialized Autonomous Swarm (OpenRouter: {'✅ Enabled' if use_openrouter else '❌ Disabled'})")

    async def run(self, session_id: str, plan: dict):
        """
        Execute Autonomous Swarm via Handoffs based on the Project Brief.
        """
        current_agent_name = plan.get("starting_agent", "ResearchAgent")
        brief = plan.get("brief", "No brief provided.")
        
        completed = {}
        iteration = 0
        max_iterations = 10 # Safety limit
        
        while current_agent_name and current_agent_name != "AssemblerAgent" and iteration < max_iterations:
            # Find Agent Class (Case-insensitive + Alias handling)
            AgentClass = None
            search_name = (current_agent_name or "").strip().lower()
            
            # Map aliases to standard agent names
            aliases = {
                "pythonscriptwriter": "BackendAgent",
                "backend": "BackendAgent",
                "frontend": "FrontendAgent",
                "researcher": "ResearchAgent",
                "reviewer": "CriticAgent",
                "architect": "AssemblerAgent",
                "assembler": "AssemblerAgent",
            }
            
            resolved_name = aliases.get(search_name, current_agent_name)
            
            for agent_cls in SKILL_TO_AGENT.values():
                if agent_cls.__name__.lower() == resolved_name.lower():
                    AgentClass = agent_cls
                    break
            
            # AssemblerAgent is special (not in SKILL_TO_AGENT)
            if not AgentClass and resolved_name.lower() == "assembleragent":
                AgentClass = AssemblerAgent

            if not AgentClass:
                print(f"⚠️ Unknown agent '{current_agent_name}' (resolved as '{resolved_name}'), stopping swarm loop.")
                break
                
            task_id = f"step_{iteration}_{current_agent_name.lower()}"
            
            # Execute Agent
            result = await self._execute_agent(session_id, task_id, brief, AgentClass, completed)
            completed[task_id] = result
            
            # Extract next_agent
            next_agent = result.get("next_agent", "AssemblerAgent")
            if not next_agent or next_agent.lower() == "none" or next_agent == current_agent_name:
                next_agent = "AssemblerAgent"
                
            print(f"🔄 [SWARM HANDOFF] {current_agent_name} ➔ {next_agent}")
            current_agent_name = next_agent
            iteration += 1

        # ── Final Assembly ─────────────────────────────────────────────────
        assembler = AssemblerAgent(self.gemini, self.memory, use_openrouter=self.use_openrouter)
        print(f"🏗️ [ORCHESTRATOR] Agent 'AssemblerAgent' initialized for final assembly")
        agent_registry.mark_busy(AGENT_REGISTRY_ID[AssemblerAgent])
        
        all_outputs = await self.memory.get_all(session_id)
        try:
            asm_result = await assembler.execute(
                session_id,
                {"outputs": all_outputs, "review": {}},
            )
            await self._write_audit(
                session_id=session_id,
                task_id="assembly",
                agent_name="AssemblerAgent",
                skill_tag="assembly",
                output=asm_result,
            )
        except Exception as e:
            print(f"⚠️ [ORCHESTRATOR] Assembly failed: {e}")
            asm_result = {"error": str(e), "summary": "Assembly failed due to an error.", "final_content": ""}
            await self.memory.publish_event(session_id, {
                "agent": "AssemblerAgent",
                "type": "TASK_FAILED",
                "data": {"task_id": "assembly", "error": str(e)},
            })
        finally:
            agent_registry.mark_idle(AGENT_REGISTRY_ID[AssemblerAgent])


    async def _execute_agent(
        self,
        session_id: str,
        task_id: str,
        brief: str,
        AgentClass,
        completed: dict,
    ):
        agent_name = AgentClass.__name__
        registry_id = AGENT_REGISTRY_ID.get(AgentClass, "")
        skill_tag = AgentClass.skill_tags[0] if AgentClass.skill_tags else "content"

        if registry_id:
            agent_registry.mark_busy(registry_id)

        await self.memory.publish_event(session_id, {
            "agent": agent_name,
            "type": "TASK_STARTED",
            "data": {
                "task_id": task_id,
                "description": f"Swarm Step: {agent_name} acting on brief.",
                "skill_tag": skill_tag,
            },
        })

        try:
            agent = AgentClass(self.gemini, self.memory, use_openrouter=self.use_openrouter)
            model_id = getattr(agent.gemini, "model", None)
            model_suffix = f" **{model_id}** is assigned." if model_id else ""

            await self.memory.publish_event(session_id, {
                "agent": agent_name,
                "type": "AGENT_INITIALIZED",
                "data": {
                    "message": f"🤖 Agent **{agent_name}** is starting.{model_suffix}",
                    "task_id": task_id,
                    "model": model_id if isinstance(model_id, str) else None,
                },
            })
            
            print(f"🤖 [SWARM] {agent_name} STARTING step {task_id}")
            result = await agent.execute(session_id, {
                "task_id": task_id,
                "description": f"Project Brief:\n{brief}",
                "skill_tag": skill_tag,
                "context": completed,
            })
            
            await self._write_audit(
                session_id=session_id,
                task_id=task_id,
                agent_name=agent_name,
                skill_tag=skill_tag,
                output=result,
            )

            await self.memory.publish_event(session_id, {
                "agent": agent_name,
                "type": "TASK_COMPLETE",
                "data": {
                    "task_id": task_id,
                    "summary": result.get("summary", ""),
                    "content": result.get("content", ""),
                    "files": result.get("files", []),
                },
            })
            
            return result
        except Exception as exc:
            await self.memory.publish_event(session_id, {
                "agent": agent_name,
                "type": "TASK_FAILED",
                "data": {"task_id": task_id, "error": str(exc)},
            })
            return {"error": str(exc), "next_agent": "AssemblerAgent"}
        finally:
            if registry_id:
                agent_registry.mark_idle(registry_id)

    async def _write_audit(
        self,
        session_id: str,
        task_id: str,
        agent_name: str,
        skill_tag: str,
        output: dict,
        quality_score: float | None = None,
    ):
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
            print(f"[Orchestrator] audit write failed for {task_id}: {e}")
