import redis.asyncio as aioredis
import json
from app.config import settings


class MemoryStore:
    def __init__(self):
        print(f"🔌 [REDIS] Initializing connection to {settings.REDIS_URL.split('@')[-1]}...") # Obfuscate password
        self.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

    async def connect(self):
        """Verify connection to Redis."""
        try:
            await self.redis.ping()
            print("✅ [REDIS] Connected successfully")
        except Exception as e:
            print(f"❌ [REDIS] Connection failed: {str(e)}")
            # Don't raise here, allow the app to start but subsequent calls will fail
            # This helps in seeing the app logs even if Redis is down

    # ── Shared memory ────────────────────────────────────────────────────────

    async def set(self, session_id: str, key: str, value: any):
        """Write a value to the session's shared memory hash."""
        await self.redis.hset(
            f"session:{session_id}:memory", key, json.dumps(value)
        )
        # Also set a TTL of 24 h on the hash
        await self.redis.expire(f"session:{session_id}:memory", 86400)

    async def get(self, session_id: str, key: str) -> any:
        """Read a single key from shared memory."""
        raw = await self.redis.hget(f"session:{session_id}:memory", key)
        return json.loads(raw) if raw else None

    async def get_all(self, session_id: str) -> dict:
        """Return all key/value pairs for a session."""
        raw = await self.redis.hgetall(f"session:{session_id}:memory")
        return {k: json.loads(v) for k, v in raw.items()}

    async def delete_session(self, session_id: str):
        """Remove all data for a session."""
        await self.redis.delete(f"session:{session_id}:memory")

    # ── A2A message bus ──────────────────────────────────────────────────────

    async def publish_event(self, session_id: str, event: dict):
        """Publish an agent event to the session channel."""
        await self.redis.publish(
            f"session:{session_id}:events", json.dumps(event)
        )

    async def subscribe(self, session_id: str):
        """Return a PubSub handle subscribed to the session channel."""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(f"session:{session_id}:events")
        return pubsub

    # ── Session status ───────────────────────────────────────────────────────

    async def set_status(self, session_id: str, status: str):
        await self.redis.set(f"session:{session_id}:status", status, ex=86400)

    async def get_status(self, session_id: str) -> str | None:
        return await self.redis.get(f"session:{session_id}:status")


# Singleton
memory_store = MemoryStore()
