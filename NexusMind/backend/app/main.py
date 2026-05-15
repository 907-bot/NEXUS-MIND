print("🚀 NexusMind Backend is starting...")
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import tasks, stream, agents, sessions
from app.core.agent_registry import bootstrap_registry
from app.tools.tool_registry import bootstrap_tools
from app.core.mcp_manager import mcp_manager
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Replaces the deprecated @app.on_event("startup") pattern.
    """
    # ── Startup ──────────────────────────────────────────────────────────────
    print("🚀 [MAIN] Starting NexusMind API initialization...")
    
    print("📋 [MAIN] Bootstrapping agent registry & tools...")
    bootstrap_registry()
    bootstrap_tools()
    
    print("🧠 [MAIN] Initializing core services (DB, Redis, MCP)...")
    from app.core.memory_store import memory_store
    
    # Run heavy initializations in parallel to speed up port binding
    try:
        await asyncio.wait_for(
            asyncio.gather(
                init_db(),
                mcp_manager.start(),
                memory_store.connect(),
            ),
            timeout=45.0 # Total startup budget
        )
        print("✅ [MAIN] Core services initialized")
    except asyncio.TimeoutError:
        print("⚠️ [MAIN] Startup timed out - some services may be initializing in background")
    except Exception as e:
        print(f"❌ [MAIN] Startup error: {e}")
    
    print("🎯 [MAIN] Configuration Check:")
    print(f"     - Auth: {'✅ Active' if settings.ENABLE_AUTH else '⚠️ Bypassed'}")
    print(f"     - LLMs: Gemini({'✅' if settings.GEMINI_API_KEY else '❌'}), OpenRouter({'✅' if settings.OPENROUTER_API_KEY else '❌'})")
    
    print("✅ NexusMind API FULLY STARTED — Ready for requests!")

    yield  # Application runs

    # ── Shutdown ─────────────────────────────────────────────────────────────
    await mcp_manager.stop()   # Close MCP connections
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
    allow_origins=["*"],
    allow_credentials=False,  # Bearer tokens don't require credentials/cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(tasks.router)
app.include_router(stream.router)
app.include_router(agents.router)
app.include_router(sessions.router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to NexusMind API",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", tags=["health"])
async def health():
    return {
        "status": "ok",
        "service": "NexusMind",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "llm_config": {
            "gemini": bool(settings.GEMINI_API_KEY),
            "openrouter": bool(settings.OPENROUTER_API_KEY),
        }
    }
