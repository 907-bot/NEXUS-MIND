# NexusMind — Autonomous Multi-Agent Intelligence Network

NexusMind is a **Level 2 autonomous AI system** that lets you describe complex tasks in plain English and watch a team of AI agents collaborate to complete them.

## 🎯 Quick Summary

| Aspect | Description |
|--------|-------------|
| **What it is** | A platform where AI agents work together like a development team |
| **What it does** | Takes a high-level goal and breaks it into tasks executed by specialized agents |
| **Who uses it** | Developers, researchers, entrepreneurs, analysts |
| **What you get** | Complete deliverables: code, reports, dashboards, research |

## 🤖 Meet the Agents

| Agent | Role | What It Does |
|-------|------|--------------|
| **PlannerAgent** | Coordinator | Breaks your goal into subtasks and plans execution |
| **ResearchAgent** | Investigator | Searches web, scrapes pages, finds data |
| **BackendAgent** | Engineer | Writes Python, FastAPI, database code |
| **FrontendAgent** | Designer | Builds React, Next.js, TypeScript interfaces |
| **DataAgent** | Analyst | Processes data, generates charts, SQL queries |
| **DevOpsAgent** | Infrastructure | Creates Docker, CI/CD, deployment configs |
| **ContentAgent** | Writer | Creates documentation, reports, summaries |
| **CriticAgent** | QA | Reviews outputs, catches bugs, ensures quality |
| **AssemblerAgent** | Integrator | Combines everything into final deliverable |

## 🧩 How It Works

### The Flow

```
1. YOU → Describe a goal in plain English
   "Build a Tesla competitor analysis report with market data"

2. PLANNER → Creates execution plan
   "Need: Research → Analysis → Report"

3. AGENTS → Execute in sequence/handoff
   ResearchAgent → DataAgent → ContentAgent

4. AGENTS → Communicate with each other (A2A)
   FrontendAgent asks BackendAgent for API specs

5. CRITIC → Reviews quality
   "Found issues: Missing citations, outdated data"

6. ASSEMBLER → Creates final deliverable
   Download as ZIP or copy the report
```

### A2A: Agent-to-Agent Communication

Agents don't just run in isolation—they talk to each other:

```
FrontendAgent ──asks──▶ BackendAgent
   "What APIs should I call?"          │
                    ◀──responds───────┘
                    "POST /api/orders"
```

This means agents share context automatically—no manual copy-pasting!

## 🔧 Technical Architecture

### Stack

| Layer | Technology |
|-------|------------|
| **AI** | Google Gemini 1.5 Flash + OpenRouter (free models) |
| **Backend** | Python 3.11, FastAPI, Redis, PostgreSQL |
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS |
| **Auth** | Clerk (JWT/OIDC) |
| **Protocols** | A2A (Agent-to-Agent), MCP (Tool access) |

### Agent Communication

All agents communicate using **TOON (Token Oriented Object Notation)**:

```toon
:from_agent "FrontendAgent"
:to_agent "BackendAgent"
:type "INFORMATION_REQUEST"
:payload :object
  :request "What API endpoints do I need?"
:end
```

TOON is more readable than JSON for debugging agent conversations.

## 🏃 Run Locally

### Prerequisites
- Python 3.11+
- Node.js 18+
- Redis (or use managed Redis)
- API keys: Gemini, OpenRouter, Clerk

### Backend
```bash
cd NexusMind/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd NexusMind/frontend
npm install
npm run dev
```

Visit `http://localhost:3000`

## 🌐 Live Demo

- **Frontend**: https://907-bot.github.io/NEXUS-MIND/dashboard/
- **API**: https://nexusmind-api.onrender.com/

## 📚 Documentation

- [Overview](./Overview.md) - Detailed architecture and use cases
- [/docs](./docs/) - Additional documentation

## 📁 Project Structure

```
NexusMind/
├── backend/
│   └── app/
│       ├── agents/          # All 9 agents
│       ├── core/           # LLM clients, memory, messaging
│       ├── api/            # FastAPI routes
│       └── tools/           # MCP tools (web search, code exec)
├── frontend/
│   └── app/
│       ├── dashboard/       # Main UI
│       └── components/      # Reusable components
└── README.md
```

## ✨ Key Features

| Feature | Why It Matters |
|---------|----------------|
| **Real-Time SSE** | Watch agents work live in your browser |
| **A2A Protocol** | Agents share context automatically |
| **MCP Tools** | Web search, code execution, file writing |
| **Self-Correction** | Critic agent catches mistakes |
| **TOON Format** | Human-readable communication logs |
| **Free LLMs** | Uses OpenRouter free models (no API costs) |

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch
3. Make changes
4. Submit a PR

All contributions welcome—new agents, better prompts, UI improvements!
