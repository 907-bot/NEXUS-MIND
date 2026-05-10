from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import tasks, stream, agents, sessions
from app.core.agent_registry import bootstrap_registry
from app.tools.tool_registry import bootstrap_tools
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Replaces the deprecated @app.on_event("startup") pattern.
    """
    # ── Startup ──────────────────────────────────────────────────────────────
    bootstrap_registry()
    bootstrap_tools()          # BUG FIX: was never called — tools were unregistered
    await init_db()
    print("✅ NexusMind API started — agents registered, tools registered, DB tables created.")

    yield  # Application runs

    # ── Shutdown ─────────────────────────────────────────────────────────────
    print("🛑 NexusMind API shutting down.")


app = FastAPI(
    title="NexusMind API",
    description="Autonomous Multi-Agent Intelligence Network",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(tasks.router)
app.include_router(stream.router)
app.include_router(agents.router)
app.include_router(sessions.router)


@app.get("/health", tags=["health"])
async def health():
    return {
        "status": "ok",
        "service": "NexusMind",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
    }
