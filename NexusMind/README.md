# NexusMind — Autonomous Multi-Agent Intelligence Network

NexusMind is a Level 2 autonomous intelligence network that decomposes high-level goals into atomic subtasks, executes them using a specialized swarm of agents, and assembles a unified deliverable in real time.

## 🚀 Core Features

- **Dynamic Task Graph**: Planner agent decomposes goals into dependent subtasks (DAG).
- **Agent Swarm**: Specialized agents for Backend, Frontend, Research, Content, DevOps, and more.
- **Parallel Execution**: Orchestrator runs independent tasks concurrently for maximum speed.
- **Real-Time Streaming**: SSE-based visualization of agent communication and progress.
- **Self-Correction**: Critic agent reviews all outputs and triggers revisions if quality scores are low.
- **Premium UI**: Modern dark-mode dashboard with glassmorphism and animated activity graphs.

## 🛠️ Tech Stack

- **LLM**: Google Gemini 1.5 Flash
- **Backend**: Python 3.11 + FastAPI + Redis + PostgreSQL
- **Frontend**: Next.js 14 + Tailwind CSS + Framer Motion
- **Auth**: Clerk (OIDC/JWT)
- **Deployment**: Render (Backend) & GitHub Pages (Frontend)

## ⚡ Quick Start

### 1. Prerequisites
- Gemini API Key ([Google AI Studio](https://aistudio.google.com/))
- Clerk Application Keys ([Clerk Dashboard](https://clerk.com/))
- Redis (Local or Render Managed)

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env # Fill in your keys
uvicorn app.main:app --reload
```

### 3. Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env.local # Fill in your keys
npm run dev
```

Visit `http://localhost:3000` to start building with NexusMind.

## 📁 Project Structure

- `/backend`: FastAPI source code, agent implementations, and core engine.
- `/frontend`: Next.js application and UI components.
- `/github/workflows`: CI/CD for automated deployment.
