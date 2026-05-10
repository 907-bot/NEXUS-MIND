# NexusMind — Autonomous Multi-Agent Intelligence Network
## Complete Implementation Skill Guide

---

## TABLE OF CONTENTS

1. [Project Overview](#1-project-overview)
2. [System Capabilities](#2-system-capabilities)
3. [Agent Definitions & Responsibilities](#3-agent-definitions--responsibilities)
4. [Tech Stack & API References](#4-tech-stack--api-references)
5. [Architecture Diagram (ASCII)](#5-architecture-diagram-ascii)
6. [Folder Structure](#6-folder-structure)
7. [Backend Implementation (FastAPI + Python)](#7-backend-implementation-fastapi--python)
8. [Frontend Implementation (Next.js + React)](#8-frontend-implementation-nextjs--react)
9. [Gemini 1.5 Flash Integration](#9-gemini-15-flash-integration)
10. [Agent Workflow Engine](#10-agent-workflow-engine)
11. [Clerk Authentication Setup](#11-clerk-authentication-setup)
12. [Deployment Guide (Render + GitHub Pages)](#12-deployment-guide-render--github-pages)
13. [Environment Variables Reference](#13-environment-variables-reference)
14. [API Endpoint Reference](#14-api-endpoint-reference)
15. [Case Study: Food Delivery App Generation](#15-case-study-food-delivery-app-generation)
16. [MVP Roadmap](#16-mvp-roadmap)
17. [Security Model](#17-security-model)

---

## 1. PROJECT OVERVIEW

**NexusMind** is a Level 2 (Dynamic Task Allocation) autonomous multi-agent intelligence network. Given a high-level user goal, the system autonomously:

- Plans and decomposes the task
- Discovers and assigns specialized agents
- Enables inter-agent communication (A2A)
- Uses external tools via MCP-style tool calling
- Assembles and delivers a final result

**Core Philosophy:**
```
User Goal → Planner → Dynamic Task Graph → Agent Swarm → Final Deliverable
```

---

## 2. SYSTEM CAPABILITIES

### 2.1 Core Capabilities

| Capability | Description |
|---|---|
| **Goal Decomposition** | Break any user goal into atomic subtasks |
| **Dynamic Agent Assignment** | Match subtasks to best-fit agents in real time |
| **A2A Communication** | Agents communicate through a shared message bus |
| **Parallel Execution** | Independent tasks run concurrently |
| **Tool Calling** | Agents invoke tools (search, code exec, DB, APIs) |
| **Shared Memory** | Agents read/write to a shared context store |
| **Self-Review** | Critic agent validates and corrects outputs |
| **Streaming Output** | Real-time SSE streaming of agent progress |
| **Multi-session** | Isolated workspaces per user session |
| **Audit Trail** | Full log of every agent action and decision |

### 2.2 Supported Goal Types

- **Code Generation** — Scaffold apps, write modules, generate APIs
- **Research** — Web search, summarization, competitor analysis
- **Content Creation** — Blogs, pitch decks, reports, documentation
- **Data Analysis** — Parse datasets, generate insights, produce charts
- **System Design** — Architecture diagrams, schema design, DevOps plans
- **Translation / Localization** — Multi-language content pipelines
- **Strategy** — Business analysis, feature planning, roadmaps

---

## 3. AGENT DEFINITIONS & RESPONSIBILITIES

### 3.1 Core Agents (Always Present)

#### 🧠 Planner Agent
- **Role**: Receives user goal → produces a JSON task graph
- **Input**: Raw user goal string
- **Output**: `TaskGraph` with subtasks, dependencies, required skill tags
- **LLM Prompt Style**: Chain-of-thought planning prompt
- **Tools**: None (pure LLM reasoning)

```python
PLANNER_SYSTEM_PROMPT = """
You are a task planning AI. Given a user goal, decompose it into atomic subtasks.
Output ONLY a valid JSON array of tasks with fields:
- task_id (string)
- description (string)
- skill_tag (one of: backend, frontend, research, data, content, review, devops)
- depends_on (list of task_ids, empty if none)
- priority (1=high, 2=medium, 3=low)
"""
```

#### 🔀 Orchestrator Agent
- **Role**: Manages the task graph execution lifecycle
- **Responsibilities**:
  - Resolves task dependencies (topological sort)
  - Dispatches tasks to appropriate specialized agents
  - Monitors completion, retries on failure
  - Aggregates outputs into shared memory
- **Tools**: Internal task queue, agent registry, shared memory

#### 🔍 Critic / Review Agent
- **Role**: Validates outputs before final delivery
- **Responsibilities**:
  - Checks for correctness, completeness, consistency
  - Flags issues and sends correction tasks back
  - Assigns quality score (0-100)
- **Max revision cycles**: 2

#### 🧩 Assembler Agent
- **Role**: Merges all agent outputs into a coherent final deliverable
- **Input**: All completed task outputs from shared memory
- **Output**: Unified response (markdown, code, JSON, or structured report)

---

### 3.2 Specialized Agents

#### 💻 Backend Agent
- **Skill Tag**: `backend`
- **Capabilities**: REST API design, database schema, server logic, auth flows
- **Tools**: Code formatter, syntax checker
- **Gemini Prompt Focus**: "Write production-ready Python/Node.js backend code"

#### 🎨 Frontend Agent
- **Skill Tag**: `frontend`
- **Capabilities**: React components, UI layout, Tailwind CSS, Next.js pages
- **Tools**: Component validator
- **Gemini Prompt Focus**: "Write clean, accessible React/Next.js code"

#### 🔬 Research Agent
- **Skill Tag**: `research`
- **Capabilities**: Web search, summarization, fact extraction, competitive analysis
- **Tools**: Google Search API, web scraper
- **Gemini Prompt Focus**: "Research and synthesize information accurately"

#### 📊 Data Agent
- **Skill Tag**: `data`
- **Capabilities**: CSV parsing, statistical analysis, chart generation, SQL queries
- **Tools**: Pandas executor, chart renderer (matplotlib)
- **Gemini Prompt Focus**: "Analyze data and produce clear insights"

#### ✍️ Content Agent
- **Skill Tag**: `content`
- **Capabilities**: Blog posts, documentation, pitch decks, marketing copy
- **Tools**: None (pure LLM generation)
- **Gemini Prompt Focus**: "Write professional, engaging content"

#### ⚙️ DevOps Agent
- **Skill Tag**: `devops`
- **Capabilities**: Dockerfile generation, CI/CD YAML, deployment scripts, infra plans
- **Tools**: YAML validator
- **Gemini Prompt Focus**: "Generate production-grade DevOps configurations"

---

### 3.3 Agent Registry Schema

```json
{
  "agents": [
    {
      "agent_id": "backend_agent_v1",
      "name": "Backend Agent",
      "skill_tags": ["backend", "database", "api"],
      "status": "idle",
      "max_concurrent_tasks": 3,
      "avg_completion_time_ms": 4200,
      "success_rate": 0.94
    }
  ]
}
```

---

## 4. TECH STACK & API REFERENCES

### 4.1 Full Stack

| Layer | Technology | Purpose |
|---|---|---|
| **LLM** | Google Gemini 1.5 Flash | Agent reasoning & generation |
| **Backend** | Python 3.11 + FastAPI | API server, orchestration engine |
| **Frontend** | Next.js 14 + React 18 | User interface |
| **Auth** | Clerk | Authentication & session management |
| **Task Queue** | Redis + asyncio | Async task dispatch |
| **Memory** | Redis Hash + JSON | Shared agent memory store |
| **Database** | PostgreSQL (via Render) | Persistent sessions & audit logs |
| **Realtime** | Server-Sent Events (SSE) | Streaming agent progress |
| **Deployment BE** | Render.com | FastAPI backend hosting |
| **Deployment FE** | GitHub Pages | Next.js static export |
| **Styling** | Tailwind CSS | UI design system |

---

### 4.2 API References

#### Google Gemini 1.5 Flash

- **Library**: `google-generativeai` (Python SDK)
- **Install**: `pip install google-generativeai`
- **Model ID**: `gemini-1.5-flash`
- **Docs**: https://ai.google.dev/api/python/google/generativeai
- **Rate Limits**: 15 RPM (free tier), 1000 RPM (paid)
- **Context Window**: 1,048,576 tokens
- **Max Output**: 8,192 tokens

```python
import google.generativeai as genai

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

response = model.generate_content(
    contents=[{"role": "user", "parts": [{"text": prompt}]}],
    generation_config=genai.GenerationConfig(
        temperature=0.7,
        max_output_tokens=2048,
        response_mime_type="application/json"  # for structured outputs
    )
)
```

#### Clerk Authentication

- **Frontend SDK**: `@clerk/nextjs`
- **Backend SDK**: `clerk-sdk-python` or JWT verification
- **Install FE**: `npm install @clerk/nextjs`
- **Docs**: https://clerk.com/docs
- **Key Concepts**: `ClerkProvider`, `useAuth()`, `useUser()`, `auth()` server-side

#### Redis (via Upstash or Render Redis)

- **Library**: `redis-py` (async)
- **Install**: `pip install redis`
- **Usage**: Task queue, shared memory, pub/sub for A2A

#### FastAPI

- **Install**: `pip install fastapi uvicorn`
- **Docs**: https://fastapi.tiangolo.com
- **Key Features**: Async routes, WebSocket, BackgroundTasks, Dependency Injection

#### PostgreSQL (asyncpg + SQLAlchemy)

- **Install**: `pip install asyncpg sqlalchemy[asyncio] alembic`
- **Used for**: Sessions, task audit logs, user workspaces

---

## 5. ARCHITECTURE DIAGRAM (ASCII)

```
┌─────────────────────────────────────────────────────────────┐
│                     NEXUSMIND SYSTEM                        │
│                                                             │
│  ┌──────────┐    ┌─────────────────────────────────────┐   │
│  │  Next.js  │    │           FastAPI Backend             │   │
│  │ (GitHub   │───▶│                                     │   │
│  │  Pages)   │    │  ┌─────────┐    ┌───────────────┐  │   │
│  │           │◀───│  │   API   │    │  Orchestrator  │  │   │
│  │ Clerk     │    │  │ Routes  │───▶│    Engine     │  │   │
│  │ Auth      │    │  └─────────┘    └──────┬────────┘  │   │
│  └──────────┘    │                         │            │   │
│                  │  ┌──────────────────────▼──────┐    │   │
│                  │  │        Agent Registry         │    │   │
│                  │  │                              │    │   │
│                  │  │  ┌─────┐ ┌──────┐ ┌──────┐  │    │   │
│                  │  │  │Plan │ │Back  │ │Front │  │    │   │
│                  │  │  │ner  │ │end   │ │ end  │  │    │   │
│                  │  │  └──┬──┘ └──┬───┘ └──┬───┘  │    │   │
│                  │  │     │       │         │      │    │   │
│                  │  │  ┌──▼───────▼─────────▼──┐   │    │   │
│                  │  │  │   A2A Message Bus      │   │    │   │
│                  │  │  │   (Redis Pub/Sub)       │   │    │   │
│                  │  │  └──────────┬─────────────┘   │    │   │
│                  │  └────────────│──────────────────┘    │   │
│                  │               │                        │   │
│                  │  ┌────────────▼───────────────────┐   │   │
│                  │  │       Shared Memory Store        │   │   │
│                  │  │   (Redis Hash per session_id)    │   │   │
│                  │  └────────────────────────────────┘   │   │
│                  │                                        │   │
│                  │  ┌──────────────────────────────────┐  │   │
│                  │  │   Gemini 1.5 Flash (Google AI)    │  │   │
│                  │  │   - Each agent calls independently │  │   │
│                  │  └──────────────────────────────────┘  │   │
│                  └─────────────────────────────────────┘   │
│                                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │              PostgreSQL (Render Managed)             │    │
│  │   sessions | task_logs | agent_outputs | users       │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. FOLDER STRUCTURE

```
nexusmind/
│
├── backend/                          # FastAPI Python Backend
│   ├── app/
│   │   ├── main.py                   # FastAPI app entry
│   │   ├── config.py                 # Settings & env vars
│   │   ├── database.py               # Async DB connection
│   │   │
│   │   ├── agents/                   # Agent implementations
│   │   │   ├── __init__.py
│   │   │   ├── base_agent.py         # BaseAgent class
│   │   │   ├── planner_agent.py      # Goal decomposition
│   │   │   ├── orchestrator.py       # Task graph execution
│   │   │   ├── backend_agent.py
│   │   │   ├── frontend_agent.py
│   │   │   ├── research_agent.py
│   │   │   ├── data_agent.py
│   │   │   ├── content_agent.py
│   │   │   ├── devops_agent.py
│   │   │   ├── critic_agent.py
│   │   │   └── assembler_agent.py
│   │   │
│   │   ├── core/
│   │   │   ├── gemini_client.py      # Gemini 1.5 Flash wrapper
│   │   │   ├── memory_store.py       # Redis shared memory
│   │   │   ├── message_bus.py        # A2A pub/sub layer
│   │   │   ├── agent_registry.py     # Agent discovery
│   │   │   └── task_graph.py         # DAG execution engine
│   │   │
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── sessions.py       # Session CRUD
│   │   │   │   ├── tasks.py          # Task submission
│   │   │   │   ├── stream.py         # SSE streaming
│   │   │   │   └── agents.py         # Agent status
│   │   │   └── middleware.py         # Clerk JWT verification
│   │   │
│   │   ├── models/
│   │   │   ├── session.py
│   │   │   ├── task.py
│   │   │   └── agent_output.py
│   │   │
│   │   └── tools/                    # MCP-style tools
│   │       ├── web_search.py
│   │       ├── code_executor.py
│   │       └── file_writer.py
│   │
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── render.yaml
│   └── alembic/                      # DB migrations
│
└── frontend/                         # Next.js Frontend
    ├── app/
    │   ├── layout.tsx                # Root layout + ClerkProvider
    │   ├── page.tsx                  # Landing page
    │   ├── dashboard/
    │   │   ├── page.tsx              # Main dashboard
    │   │   └── session/[id]/
    │   │       └── page.tsx          # Active session view
    │   └── api/
    │       └── auth/
    │           └── [...clerk]/
    │               └── route.ts      # Clerk auth handler
    │
    ├── components/
    │   ├── GoalInput.tsx             # Goal submission form
    │   ├── AgentGraph.tsx            # Live agent network viz
    │   ├── TaskTimeline.tsx          # Task progress timeline
    │   ├── OutputPanel.tsx           # Final output renderer
    │   ├── AgentCard.tsx             # Individual agent status
    │   └── StreamConsumer.tsx        # SSE event handler
    │
    ├── lib/
    │   ├── api.ts                    # Backend API client
    │   └── types.ts                  # TypeScript interfaces
    │
    ├── next.config.js                # Static export config
    ├── tailwind.config.js
    └── package.json
```

---

## 7. BACKEND IMPLEMENTATION (FastAPI + Python)

### 7.1 `requirements.txt`

```txt
fastapi==0.111.0
uvicorn[standard]==0.29.0
google-generativeai==0.7.0
redis==5.0.4
asyncpg==0.29.0
sqlalchemy[asyncio]==2.0.30
alembic==1.13.1
python-jose[cryptography]==3.3.0
httpx==0.27.0
pydantic==2.7.0
pydantic-settings==2.2.1
python-dotenv==1.0.1
sse-starlette==2.1.0
```

### 7.2 `app/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Google AI
    GEMINI_API_KEY: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # PostgreSQL
    DATABASE_URL: str

    # Clerk
    CLERK_SECRET_KEY: str
    CLERK_PUBLISHABLE_KEY: str
    CLERK_JWT_ISSUER: str  # e.g. https://your-app.clerk.accounts.dev

    # App
    APP_ENV: str = "development"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"

settings = Settings()
```

### 7.3 `app/core/gemini_client.py`

```python
import google.generativeai as genai
from app.config import settings
import json, re

genai.configure(api_key=settings.GEMINI_API_KEY)

class GeminiClient:
    def __init__(self, temperature: float = 0.7, max_tokens: int = 2048):
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

    async def generate(self, system_prompt: str, user_message: str) -> str:
        """Generate text response."""
        full_prompt = f"{system_prompt}\n\n{user_message}"
        response = self.model.generate_content(
            contents=full_prompt,
            generation_config=self.config
        )
        return response.text

    async def generate_json(self, system_prompt: str, user_message: str) -> dict | list:
        """Generate and parse JSON response."""
        json_prompt = system_prompt + "\nRespond ONLY with valid JSON. No markdown, no explanation."
        text = await self.generate(json_prompt, user_message)
        # Strip markdown fences if present
        text = re.sub(r"```json|```", "", text).strip()
        return json.loads(text)

gemini = GeminiClient()
```

### 7.4 `app/core/memory_store.py`

```python
import redis.asyncio as aioredis
import json
from app.config import settings

class MemoryStore:
    def __init__(self):
        self.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

    async def set(self, session_id: str, key: str, value: any):
        """Write to shared memory for a session."""
        await self.redis.hset(f"session:{session_id}:memory", key, json.dumps(value))

    async def get(self, session_id: str, key: str) -> any:
        """Read from shared memory."""
        raw = await self.redis.hget(f"session:{session_id}:memory", key)
        return json.loads(raw) if raw else None

    async def get_all(self, session_id: str) -> dict:
        """Get entire session memory."""
        raw = await self.redis.hgetall(f"session:{session_id}:memory")
        return {k: json.loads(v) for k, v in raw.items()}

    async def publish_event(self, session_id: str, event: dict):
        """Publish agent event to A2A bus."""
        await self.redis.publish(f"session:{session_id}:events", json.dumps(event))

    async def subscribe(self, session_id: str):
        """Subscribe to session events (for SSE streaming)."""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(f"session:{session_id}:events")
        return pubsub

memory_store = MemoryStore()
```

### 7.5 `app/agents/base_agent.py`

```python
from abc import ABC, abstractmethod
from app.core.gemini_client import GeminiClient
from app.core.memory_store import MemoryStore
import time

class BaseAgent(ABC):
    name: str
    skill_tags: list[str]

    def __init__(self, gemini: GeminiClient, memory: MemoryStore):
        self.gemini = gemini
        self.memory = memory

    @abstractmethod
    async def execute(self, session_id: str, task: dict) -> dict:
        """Execute a task. Return output dict."""
        pass

    async def emit_event(self, session_id: str, event_type: str, data: dict):
        """Emit A2A event to message bus."""
        event = {
            "agent": self.name,
            "type": event_type,
            "timestamp": time.time(),
            "data": data
        }
        await self.memory.publish_event(session_id, event)
        print(f"[{self.name}] {event_type}: {data}")
```

### 7.6 `app/agents/planner_agent.py`

```python
from app.agents.base_agent import BaseAgent

PLANNER_SYSTEM = """
You are a master project planner AI. Given a user goal, decompose it into atomic subtasks.
Output ONLY a JSON array. Each task object must have:
- task_id: unique string (e.g. "task_001")
- description: clear instruction for the agent
- skill_tag: exactly one of [backend, frontend, research, data, content, devops, review]
- depends_on: list of task_ids this task waits for (empty list if none)
- priority: integer 1 (high) to 3 (low)
Do NOT include any text outside the JSON array.
"""

class PlannerAgent(BaseAgent):
    name = "PlannerAgent"
    skill_tags = ["planning"]

    async def execute(self, session_id: str, task: dict) -> dict:
        goal = task.get("goal", "")
        await self.emit_event(session_id, "PLANNING_STARTED", {"goal": goal})

        task_graph = await self.gemini.generate_json(PLANNER_SYSTEM, f"Goal: {goal}")

        await self.memory.set(session_id, "task_graph", task_graph)
        await self.emit_event(session_id, "PLANNING_COMPLETE", {
            "task_count": len(task_graph)
        })

        return {"task_graph": task_graph}
```

### 7.7 `app/agents/orchestrator.py`

```python
from app.agents.base_agent import BaseAgent
from app.agents.backend_agent import BackendAgent
from app.agents.frontend_agent import FrontendAgent
from app.agents.research_agent import ResearchAgent
from app.agents.content_agent import ContentAgent
from app.agents.devops_agent import DevOpsAgent
from app.agents.critic_agent import CriticAgent
from app.agents.assembler_agent import AssemblerAgent
from app.core.gemini_client import GeminiClient
from app.core.memory_store import MemoryStore
import asyncio

SKILL_TO_AGENT = {
    "backend": BackendAgent,
    "frontend": FrontendAgent,
    "research": ResearchAgent,
    "content": ContentAgent,
    "devops": DevOpsAgent,
    "data": BackendAgent,   # Fallback to backend for data tasks
    "review": CriticAgent,
}

class Orchestrator:
    def __init__(self, gemini: GeminiClient, memory: MemoryStore):
        self.gemini = gemini
        self.memory = memory

    async def run(self, session_id: str, task_graph: list[dict]):
        """Execute the task graph respecting dependencies."""
        completed = {}
        remaining = list(task_graph)

        while remaining:
            # Find tasks whose dependencies are all satisfied
            ready = [
                t for t in remaining
                if all(dep in completed for dep in t.get("depends_on", []))
            ]

            if not ready:
                # Circular dependency or stuck — break
                break

            # Execute ready tasks in parallel
            await asyncio.gather(*[
                self._run_task(session_id, task, completed)
                for task in ready
            ])

            for task in ready:
                remaining.remove(task)

        # Critic review pass
        await self._review_pass(session_id, completed)

        # Final assembly
        await self._assemble(session_id, completed)

    async def _run_task(self, session_id: str, task: dict, completed: dict):
        skill = task.get("skill_tag", "content")
        AgentClass = SKILL_TO_AGENT.get(skill, ContentAgent)
        agent = AgentClass(self.gemini, self.memory)

        await self.memory.publish_event(session_id, {
            "agent": agent.name,
            "type": "TASK_STARTED",
            "data": {"task_id": task["task_id"], "description": task["description"]}
        })

        result = await agent.execute(session_id, task)
        completed[task["task_id"]] = result

        await self.memory.set(session_id, f"output:{task['task_id']}", result)
        await self.memory.publish_event(session_id, {
            "agent": agent.name,
            "type": "TASK_COMPLETE",
            "data": {"task_id": task["task_id"]}
        })

    async def _review_pass(self, session_id: str, completed: dict):
        critic = CriticAgent(self.gemini, self.memory)
        all_outputs = await self.memory.get_all(session_id)
        await critic.execute(session_id, {"outputs": all_outputs})

    async def _assemble(self, session_id: str, completed: dict):
        assembler = AssemblerAgent(self.gemini, self.memory)
        all_outputs = await self.memory.get_all(session_id)
        await assembler.execute(session_id, {"outputs": all_outputs})
```

### 7.8 `app/api/routes/tasks.py`

```python
from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from app.agents.planner_agent import PlannerAgent
from app.agents.orchestrator import Orchestrator
from app.core.gemini_client import GeminiClient
from app.core.memory_store import MemoryStore
from app.api.middleware import get_current_user
import uuid

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

class GoalRequest(BaseModel):
    goal: str

async def run_nexusmind_pipeline(session_id: str, goal: str):
    gemini = GeminiClient()
    memory = MemoryStore()

    # Step 1: Plan
    planner = PlannerAgent(gemini, memory)
    result = await planner.execute(session_id, {"goal": goal})
    task_graph = result["task_graph"]

    # Step 2: Orchestrate
    orchestrator = Orchestrator(gemini, memory)
    await orchestrator.run(session_id, task_graph)

@router.post("/submit")
async def submit_goal(
    request: GoalRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user)
):
    session_id = str(uuid.uuid4())
    background_tasks.add_task(run_nexusmind_pipeline, session_id, request.goal)
    return {"session_id": session_id, "status": "processing"}
```

### 7.9 `app/api/routes/stream.py` (SSE Streaming)

```python
from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse
from app.core.memory_store import MemoryStore
from app.api.middleware import get_current_user
import asyncio, json

router = APIRouter(prefix="/api/stream", tags=["stream"])
memory = MemoryStore()

@router.get("/{session_id}")
async def stream_session(session_id: str, user=Depends(get_current_user)):
    async def event_generator():
        pubsub = await memory.subscribe(session_id)
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    yield {"data": message["data"]}
                await asyncio.sleep(0.01)
        finally:
            await pubsub.unsubscribe()

    return EventSourceResponse(event_generator())
```

### 7.10 `app/api/middleware.py` (Clerk JWT Verification)

```python
from fastapi import HTTPException, Header
from jose import jwt, JWTError
import httpx
from app.config import settings

async def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")

    token = authorization.split(" ")[1]
    try:
        # Fetch Clerk JWKS
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{settings.CLERK_JWT_ISSUER}/.well-known/jwks.json")
            jwks = resp.json()

        # Verify token (simplified - use python-jose with JWKS in production)
        payload = jwt.decode(token, jwks, algorithms=["RS256"])
        return {"user_id": payload.get("sub"), "email": payload.get("email")}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### 7.11 `app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import tasks, stream, agents, sessions

app = FastAPI(title="NexusMind API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router)
app.include_router(stream.router)
app.include_router(agents.router)
app.include_router(sessions.router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "NexusMind"}
```

---

## 8. FRONTEND IMPLEMENTATION (Next.js + React)

### 8.1 `package.json` (key dependencies)

```json
{
  "dependencies": {
    "next": "14.2.3",
    "react": "^18",
    "@clerk/nextjs": "^5.1.4",
    "tailwindcss": "^3.4.3",
    "axios": "^1.7.2",
    "lucide-react": "^0.383.0",
    "react-markdown": "^9.0.1",
    "framer-motion": "^11.2.10"
  }
}
```

### 8.2 `app/layout.tsx`

```tsx
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider publishableKey={process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY!}>
      <html lang="en">
        <body className="bg-gray-950 text-gray-100">{children}</body>
      </html>
    </ClerkProvider>
  );
}
```

### 8.3 `app/dashboard/page.tsx`

```tsx
"use client";
import { useAuth } from "@clerk/nextjs";
import { useState } from "react";
import GoalInput from "@/components/GoalInput";
import TaskTimeline from "@/components/TaskTimeline";
import OutputPanel from "@/components/OutputPanel";
import AgentGraph from "@/components/AgentGraph";
import { submitGoal } from "@/lib/api";

export default function Dashboard() {
  const { getToken } = useAuth();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [output, setOutput] = useState<string>("");

  const handleSubmit = async (goal: string) => {
    const token = await getToken();
    const { session_id } = await submitGoal(goal, token!);
    setSessionId(session_id);
    startStreaming(session_id, token!);
  };

  const startStreaming = (sid: string, token: string) => {
    const url = `${process.env.NEXT_PUBLIC_API_URL}/api/stream/${sid}`;
    const es = new EventSource(url + `?token=${token}`);

    es.onmessage = (e) => {
      const event = JSON.parse(e.data);
      setEvents((prev) => [...prev, event]);
      if (event.type === "FINAL_OUTPUT") {
        setOutput(event.data.content);
        es.close();
      }
    };
  };

  return (
    <div className="min-h-screen p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-8 text-purple-400">NexusMind</h1>
      <GoalInput onSubmit={handleSubmit} />
      {sessionId && (
        <div className="grid grid-cols-2 gap-6 mt-8">
          <div>
            <AgentGraph events={events} />
            <TaskTimeline events={events} />
          </div>
          <OutputPanel content={output} />
        </div>
      )}
    </div>
  );
}
```

### 8.4 `lib/api.ts`

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function submitGoal(goal: string, token: string) {
  const res = await fetch(`${API_URL}/api/tasks/submit`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ goal }),
  });
  return res.json();
}

export async function getSessionOutput(sessionId: string, token: string) {
  const res = await fetch(`${API_URL}/api/sessions/${sessionId}/output`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.json();
}
```

### 8.5 `next.config.js` (Static Export for GitHub Pages)

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  basePath: process.env.NODE_ENV === "production" ? "/nexusmind" : "",
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY,
  },
};

module.exports = nextConfig;
```

---

## 9. GEMINI 1.5 FLASH INTEGRATION

### 9.1 Per-Agent Prompt Templates

#### Backend Agent Prompt
```python
BACKEND_SYSTEM = """
You are an expert backend engineer. Given a task, produce production-ready code.
Format your response as JSON:
{
  "files": [
    {"filename": "api/routes/orders.py", "content": "...code..."},
  ],
  "summary": "What was built",
  "dependencies": ["fastapi", "sqlalchemy"]
}
"""
```

#### Research Agent Prompt
```python
RESEARCH_SYSTEM = """
You are a research analyst. Given a topic, provide structured research.
Format as JSON:
{
  "findings": ["key insight 1", "key insight 2"],
  "sources": ["URL or reference"],
  "summary": "2-3 sentence synthesis",
  "recommendations": ["action 1", "action 2"]
}
"""
```

#### Critic Agent Prompt
```python
CRITIC_SYSTEM = """
You are a strict quality reviewer. Review the provided outputs and identify:
1. Missing components
2. Logical errors
3. Security vulnerabilities
4. Consistency issues
Format as JSON:
{
  "score": 85,
  "issues": [{"task_id": "...", "issue": "...", "severity": "high|medium|low"}],
  "approved": true
}
"""
```

### 9.2 Gemini Safety Settings Override (for code generation)

```python
from google.generativeai.types import HarmCategory, HarmBlockThreshold

safety_settings = {
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}

model = genai.GenerativeModel(
    "gemini-1.5-flash",
    safety_settings=safety_settings
)
```

### 9.3 Retry Logic for Rate Limits

```python
import asyncio
from google.api_core.exceptions import ResourceExhausted

async def generate_with_retry(model, prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except ResourceExhausted:
            wait = 2 ** attempt  # Exponential backoff
            await asyncio.sleep(wait)
    raise Exception("Gemini rate limit exceeded after retries")
```

---

## 10. AGENT WORKFLOW ENGINE

### 10.1 Task Graph Example (JSON)

```json
[
  {
    "task_id": "t001",
    "description": "Design PostgreSQL database schema for a food delivery app",
    "skill_tag": "backend",
    "depends_on": [],
    "priority": 1
  },
  {
    "task_id": "t002",
    "description": "Design REST API endpoints for orders, users, restaurants",
    "skill_tag": "backend",
    "depends_on": ["t001"],
    "priority": 1
  },
  {
    "task_id": "t003",
    "description": "Create React component structure for the customer app",
    "skill_tag": "frontend",
    "depends_on": [],
    "priority": 2
  },
  {
    "task_id": "t004",
    "description": "Write Dockerfile and docker-compose for the full stack",
    "skill_tag": "devops",
    "depends_on": ["t001", "t002"],
    "priority": 2
  },
  {
    "task_id": "t005",
    "description": "Review all outputs for completeness and correctness",
    "skill_tag": "review",
    "depends_on": ["t001", "t002", "t003", "t004"],
    "priority": 1
  }
]
```

### 10.2 Execution Timeline

```
t=0s   [Planner]   Goal received → task_graph generated (5 tasks)
t=2s   [Orch]      t001, t003 dispatched (no deps) — PARALLEL
t=8s   [Backend]   t001 complete → schema output stored
t=9s   [Frontend]  t003 complete → components output stored
t=10s  [Orch]      t002 dispatched (dep t001 satisfied)
t=10s  [Orch]      t004 dispatched (deps t001 satisfied, t002 pending — held)
t=16s  [Backend]   t002 complete → API spec stored
t=17s  [Orch]      t004 dispatched (all deps satisfied)
t=22s  [DevOps]    t004 complete → Docker files stored
t=23s  [Critic]    t005 dispatched → reviews all outputs
t=26s  [Critic]    Score: 87/100, minor issues flagged
t=28s  [Assembler] Final output merged and emitted
```

### 10.3 A2A Message Format

```json
{
  "message_id": "msg_abc123",
  "from_agent": "FrontendAgent",
  "to_agent": "BackendAgent",
  "session_id": "sess_xyz",
  "type": "INFORMATION_REQUEST",
  "timestamp": 1715000000.0,
  "payload": {
    "request": "What is the API endpoint structure for the orders resource?",
    "context": "Building the OrderList component and need to know fetch URL"
  }
}
```

---

## 11. CLERK AUTHENTICATION SETUP

### 11.1 Clerk Dashboard Configuration

1. Create app at https://clerk.com
2. Set **Allowed redirect URLs**: `https://yourusername.github.io/nexusmind/*`
3. Enable **Email + Password** + **Google OAuth**
4. Note: `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY`

### 11.2 Protected Routes (Next.js middleware)

```typescript
// middleware.ts (root of Next.js project)
import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isPublicRoute = createRouteMatcher(["/", "/sign-in(.*)", "/sign-up(.*)"]);

export default clerkMiddleware((auth, req) => {
  if (!isPublicRoute(req)) auth().protect();
});

export const config = {
  matcher: ["/((?!_next|.*\\..*).*)"],
};
```

### 11.3 Auth UI Components

```tsx
// components/AuthButtons.tsx
import { SignInButton, SignUpButton, UserButton, useAuth } from "@clerk/nextjs";

export default function AuthButtons() {
  const { isSignedIn } = useAuth();
  return isSignedIn ? (
    <UserButton afterSignOutUrl="/" />
  ) : (
    <div className="flex gap-2">
      <SignInButton mode="modal">
        <button className="px-4 py-2 bg-purple-600 rounded-lg">Sign In</button>
      </SignInButton>
      <SignUpButton mode="modal">
        <button className="px-4 py-2 border border-purple-600 rounded-lg">Sign Up</button>
      </SignUpButton>
    </div>
  );
}
```

---

## 12. DEPLOYMENT GUIDE (Render + GitHub Pages)

### 12.1 Backend → Render.com

**`render.yaml`** (place in `/backend/`)

```yaml
services:
  - type: web
    name: nexusmind-api
    env: python
    buildCommand: pip install -r requirements.txt && alembic upgrade head
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2
    plan: starter
    envVars:
      - key: GEMINI_API_KEY
        sync: false
      - key: REDIS_URL
        fromService:
          name: nexusmind-redis
          type: redis
          property: connectionString
      - key: DATABASE_URL
        fromDatabase:
          name: nexusmind-db
          property: connectionString
      - key: CLERK_SECRET_KEY
        sync: false
      - key: CLERK_JWT_ISSUER
        sync: false
      - key: CORS_ORIGINS
        value: "https://yourusername.github.io"

  - type: redis
    name: nexusmind-redis
    plan: starter
    maxmemoryPolicy: allkeys-lru

databases:
  - name: nexusmind-db
    plan: starter
```

**Deployment Steps:**
1. Push backend code to GitHub
2. Go to render.com → New → Blueprint
3. Connect GitHub repo
4. Select `render.yaml`
5. Add secret env vars in Render dashboard
6. Deploy → note the service URL (e.g., `https://nexusmind-api.onrender.com`)

### 12.2 Frontend → GitHub Pages

**`.github/workflows/deploy.yml`**

```yaml
name: Deploy NexusMind Frontend

on:
  push:
    branches: [main]
    paths:
      - "frontend/**"

jobs:
  deploy:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./frontend

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"

      - run: npm ci

      - name: Build
        run: npm run build
        env:
          NEXT_PUBLIC_API_URL: ${{ secrets.NEXT_PUBLIC_API_URL }}
          NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: ${{ secrets.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY }}

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./frontend/out
          destination_dir: nexusmind
```

**GitHub Repository Settings:**
1. Settings → Pages → Source: `gh-pages` branch
2. Add Secrets: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
3. Site URL: `https://yourusername.github.io/nexusmind`

### 12.3 Deployment Checklist

```
Backend (Render)
☐ Redis service created
☐ PostgreSQL database created
☐ Web service deployed
☐ All env vars set
☐ Health check passing: GET /health
☐ CORS set to GitHub Pages URL

Frontend (GitHub Pages)
☐ next.config.js has output: "export"
☐ basePath set correctly
☐ GitHub Actions workflow added
☐ Repository secrets set
☐ Clerk redirect URLs updated
☐ Build successful, pages live
```

---

## 13. ENVIRONMENT VARIABLES REFERENCE

### Backend `.env`

```env
# Google AI
GEMINI_API_KEY=AIza...

# Redis
REDIS_URL=redis://localhost:6379

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/nexusmind

# Clerk
CLERK_SECRET_KEY=sk_live_...
CLERK_JWT_ISSUER=https://your-app.clerk.accounts.dev

# App
APP_ENV=production
CORS_ORIGINS=["https://yourusername.github.io"]
```

### Frontend `.env.local`

```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
NEXT_PUBLIC_API_URL=https://nexusmind-api.onrender.com
CLERK_SECRET_KEY=sk_live_...
```

---

## 14. API ENDPOINT REFERENCE

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | None | Service health check |
| `POST` | `/api/tasks/submit` | Clerk JWT | Submit a new goal |
| `GET` | `/api/stream/{session_id}` | Clerk JWT | SSE stream of agent events |
| `GET` | `/api/sessions/{session_id}` | Clerk JWT | Get session status |
| `GET` | `/api/sessions/{session_id}/output` | Clerk JWT | Get final output |
| `GET` | `/api/sessions` | Clerk JWT | List user's sessions |
| `DELETE` | `/api/sessions/{session_id}` | Clerk JWT | Delete a session |
| `GET` | `/api/agents` | Clerk JWT | List all registered agents |
| `GET` | `/api/agents/{agent_id}/status` | Clerk JWT | Get agent current status |

### Request/Response Examples

**POST `/api/tasks/submit`**
```json
// Request
{ "goal": "Build a food delivery app with React frontend and FastAPI backend" }

// Response
{
  "session_id": "3f7a9b2c-...",
  "status": "processing",
  "estimated_completion_ms": 30000
}
```

**GET `/api/stream/{session_id}` (SSE)**
```
event: message
data: {"agent":"PlannerAgent","type":"PLANNING_STARTED","timestamp":1715000000,"data":{"goal":"Build..."}}

event: message
data: {"agent":"BackendAgent","type":"TASK_STARTED","timestamp":1715000002,"data":{"task_id":"t001"}}

event: message
data: {"agent":"AssemblerAgent","type":"FINAL_OUTPUT","timestamp":1715000028,"data":{"content":"# Generated Output\n..."}}
```

---

## 15. CASE STUDY: FOOD DELIVERY APP GENERATION

### Scenario
**User Input:** *"Build a food delivery mobile app with login, payment, and delivery tracking"*

### Step-by-Step Execution

---

**STEP 1 — Goal Received (t=0s)**

User submits goal via dashboard. Clerk JWT verified. Session `sess_abc123` created.

---

**STEP 2 — PlannerAgent Runs (t=0s → t=3s)**

Gemini 1.5 Flash receives:
```
Goal: Build a food delivery mobile app with login, payment, and delivery tracking
```

Planner outputs task graph:
```json
[
  {"task_id":"t001","description":"Design PostgreSQL schema: users, restaurants, orders, drivers, payments","skill_tag":"backend","depends_on":[],"priority":1},
  {"task_id":"t002","description":"Build FastAPI REST endpoints for auth, orders, restaurants, tracking","skill_tag":"backend","depends_on":["t001"],"priority":1},
  {"task_id":"t003","description":"Create Stripe payment integration service with webhooks","skill_tag":"backend","depends_on":["t001"],"priority":1},
  {"task_id":"t004","description":"Design React Native screens: Login, Home, Cart, Tracking, Profile","skill_tag":"frontend","depends_on":[],"priority":2},
  {"task_id":"t005","description":"Write real-time delivery tracking using WebSocket","skill_tag":"backend","depends_on":["t002"],"priority":1},
  {"task_id":"t006","description":"Generate Docker + CI/CD pipeline for the full stack","skill_tag":"devops","depends_on":["t001","t002"],"priority":2},
  {"task_id":"t007","description":"Review all outputs for completeness and security","skill_tag":"review","depends_on":["t001","t002","t003","t004","t005","t006"],"priority":1}
]
```
**7 tasks planned. 2 can start immediately (t001, t004).**

---

**STEP 3 — Parallel Execution Phase 1 (t=3s → t=11s)**

| Agent | Task | Output |
|---|---|---|
| BackendAgent | t001 | PostgreSQL schema (6 tables, 24 columns) |
| FrontendAgent | t004 | React Native file structure, 5 screen stubs |

---

**STEP 4 — Dependent Tasks Dispatch (t=11s → t=22s)**

| Agent | Task | Waiting For | Output |
|---|---|---|---|
| BackendAgent | t002 | t001 ✓ | 12 REST endpoints, OpenAPI spec |
| BackendAgent | t003 | t001 ✓ | Stripe integration + webhook handler |

---

**STEP 5 — A2A Communication (t=15s)**

```
FrontendAgent → BackendAgent:
  "Need the order API response schema to build the Cart component"

BackendAgent → FrontendAgent:
  {
    "endpoint": "POST /api/orders",
    "response": {
      "order_id": "uuid",
      "status": "pending",
      "estimated_delivery_minutes": 35
    }
  }
```

Frontend agent updates Cart component based on the real API schema.

---

**STEP 6 — Phase 2 Tasks (t=22s → t=27s)**

| Agent | Task | Output |
|---|---|---|
| BackendAgent | t005 | WebSocket server for GPS tracking, event types |
| DevOpsAgent | t006 | Dockerfile (multi-stage), docker-compose.yml, GitHub Actions CI |

---

**STEP 7 — Critic Review (t=27s → t=30s)**

CriticAgent reviews all 6 outputs:
```json
{
  "score": 82,
  "issues": [
    {"task_id":"t003","issue":"Missing idempotency key on Stripe charge","severity":"high"},
    {"task_id":"t002","issue":"Auth middleware not applied to /orders endpoint","severity":"high"},
    {"task_id":"t004","issue":"Missing loading states on async operations","severity":"medium"}
  ],
  "approved": false
}
```

**Orchestrator triggers correction tasks for high-severity issues.**

---

**STEP 8 — Corrections Applied (t=30s → t=34s)**

BackendAgent fixes Stripe idempotency + auth middleware.
FrontendAgent adds loading skeletons.

Critic re-reviews: **Score: 94/100 — APPROVED.**

---

**STEP 9 — Final Assembly (t=34s → t=36s)**

AssemblerAgent merges all outputs into a structured deliverable:

```markdown
# Food Delivery App — NexusMind Generated

## Database Schema
[6 table definitions with relationships]

## Backend API (FastAPI)
[12 endpoints with OpenAPI spec]

## Payment Integration
[Stripe service with idempotency, webhooks]

## Frontend (React Native)
[5 screens with navigation structure]

## Real-time Tracking
[WebSocket server implementation]

## DevOps
[Dockerfile, docker-compose, GitHub Actions CI/CD]

## Getting Started
[Step-by-step setup instructions]
```

---

**CASE STUDY METRICS**

| Metric | Value |
|---|---|
| Total execution time | 36 seconds |
| Tasks completed | 7 |
| Agents used | 4 (Backend, Frontend, DevOps, Critic) |
| Parallel task batches | 3 |
| A2A messages exchanged | 4 |
| Revision cycles | 1 |
| Final quality score | 94/100 |
| Estimated manual dev time | 3-5 days |

---

## 16. MVP ROADMAP

### Phase 1 — Foundation (Week 1-2)
- [ ] FastAPI skeleton + Gemini client
- [ ] PlannerAgent implementation
- [ ] Basic Orchestrator (sequential execution)
- [ ] Redis memory store
- [ ] Clerk auth integration
- [ ] `/submit` and `/stream` endpoints

### Phase 2 — Agent Swarm (Week 3-4)
- [ ] All 8 specialized agents implemented
- [ ] Parallel task execution (asyncio.gather)
- [ ] CriticAgent with revision loop
- [ ] AssemblerAgent
- [ ] SSE streaming to frontend

### Phase 3 — Frontend (Week 5-6)
- [ ] Next.js dashboard with Clerk
- [ ] GoalInput component
- [ ] Real-time agent progress visualization
- [ ] Output panel with markdown rendering
- [ ] Session history

### Phase 4 — Production (Week 7-8)
- [ ] Render deployment with Redis + PostgreSQL
- [ ] GitHub Pages deployment
- [ ] Rate limiting per user
- [ ] Audit logging to PostgreSQL
- [ ] Error recovery and retries

---

## 17. SECURITY MODEL

### Authentication Flow
```
User → Clerk Sign In → JWT Token → Next.js stores token
→ API request with Bearer token → FastAPI verifies via JWKS
→ user_id extracted → session scoped to user
```

### Session Isolation
- Each session has a unique `session_id` (UUID v4)
- Redis keys are namespaced: `session:{session_id}:*`
- Users can only access their own sessions (user_id checked in routes)

### API Security
- All routes (except `/health`) require valid Clerk JWT
- CORS restricted to GitHub Pages domain
- Rate limiting: 10 goal submissions per user per hour
- Input validation via Pydantic models

### Gemini API Key Protection
- Key stored as Render environment secret (never in code)
- Backend-only: never exposed to frontend
- Per-request cost tracking via token counting

### Data Retention
- Session data in Redis: TTL of 24 hours
- Audit logs in PostgreSQL: retained 30 days
- No user content stored beyond session lifetime

---

## QUICK START

```bash
# Clone repo
git clone https://github.com/yourusername/nexusmind

# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Fill in your keys
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
cp .env.local.example .env.local  # Fill in your keys
npm run dev

# Open http://localhost:3000
```

---

*NexusMind SKILL.md — Complete implementation reference for autonomous multi-agent AI systems*
*Stack: Gemini 1.5 Flash · FastAPI · Next.js · Clerk · Redis · PostgreSQL · Render · GitHub Pages*
