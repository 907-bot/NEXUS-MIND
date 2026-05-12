from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,  # Verify connections before use (handles stale connections)
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    """FastAPI dependency: yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables on startup (use Alembic migrations in production)."""
    async with engine.begin() as conn:
        # Import models via the package __init__ so all mappers are registered
        import app.models  # noqa: F401 — triggers Session, Task, AgentOutput imports
        await conn.run_sync(Base.metadata.create_all)
        
        # Self-healing migration for existing databases
        try:
            from sqlalchemy import text
            print("🛠️ [DB] Running migrations...")
            # Fix sessions table
            await conn.execute(text("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"))
            # Fix tasks table
            await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS output JSON;"))
            await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP;"))
            print("✅ [DB] Migrations applied successfully")
        except Exception as e:
            print(f"⚠️ [DB] Migration note: {e}")
            pass 
