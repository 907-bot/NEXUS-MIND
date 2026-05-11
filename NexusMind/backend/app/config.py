from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Google AI
    GEMINI_API_KEY: str
    GOOGLE_API_KEY: str = ""
    GOOGLE_SEARCH_ENGINE_ID: str = ""

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
        "*"  # Temporary: Allow all origins (remove in production for security)
    ]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
