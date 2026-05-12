from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Google AI
    GEMINI_API_KEY: str
    GOOGLE_API_KEY: str = ""
    GOOGLE_SEARCH_ENGINE_ID: str = ""

    # OpenRouter
    OPENROUTER_API_KEY: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/nexusmind"

    # Clerk
    CLERK_SECRET_KEY: str = ""
    CLERK_PUBLISHABLE_KEY: str = ""
    CLERK_JWT_ISSUER: str = ""  # e.g. https://your-app.clerk.accounts.dev

    # App
    APP_ENV: str = "development"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    ENABLE_AUTH: bool = True

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

    def __init__(self, **values):
        super().__init__(**values)
        # Handle CORS_ORIGINS parsing
        if isinstance(self.CORS_ORIGINS, str):
            import json
            try:
                # Try JSON first (e.g. '["*"]' or '["https://a.com"]')
                self.CORS_ORIGINS = json.loads(self.CORS_ORIGINS)
            except json.JSONDecodeError:
                # Fallback to comma-separated
                self.CORS_ORIGINS = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        
        # Ensure REDIS_URL has protocol
        if self.REDIS_URL and not self.REDIS_URL.startswith("redis"):
            self.REDIS_URL = f"redis://{self.REDIS_URL}"

    @property
    def async_database_url(self) -> str:
        """Fix for Render/Heroku providing postgres:// instead of postgresql+asyncpg://"""
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


settings = Settings()
# Use the fixed URL for the application
settings.DATABASE_URL = settings.async_database_url
