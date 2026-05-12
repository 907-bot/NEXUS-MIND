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
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://907-bot.github.io",
        "https://907-bot.github.io/NEXUS-MIND",
        "https://907-bot.github.io/NEXUS-MIND/",
    ]

    class Config:
        env_file = ".env"
        extra = "ignore"

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
