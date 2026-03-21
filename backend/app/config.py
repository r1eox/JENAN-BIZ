"""
Jenan BIZ — Application Configuration
Loads from .env with defaults for development.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Database ─────────────────────────────────
    # SQLite (default for local dev) or PostgreSQL for production
    DATABASE_URL: str = "sqlite+aiosqlite:///./jenanbiz.db"

    # ── Redis ────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT ──────────────────────────────────────
    JWT_SECRET_KEY: str = "dev_secret_key_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── File Uploads ─────────────────────────────
    MAX_FILE_SIZE_MB: int = 15
    UPLOAD_DIR: str = "./uploads"

    # ── Rate Limiting ────────────────────────────
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_SECONDS: int = 300  # 5 min

    # ── WhatsApp Business API ────────────────────
    WHATSAPP_API_URL: str = ""
    WHATSAPP_API_TOKEN: str = ""
    WHATSAPP_INSTANCE_ID: str = ""
    WHATSAPP_ENABLED: bool = False

    # ── App ──────────────────────────────────────
    APP_NAME: str = "Jenan BIZ"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    # Set to False in production to skip demo user creation
    SEED_DEMO_DATA: bool = True
    # ── OpenAI ───────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_ENABLED: bool = False
    # ── CORS ─────────────────────────────────────
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:5176,http://localhost:3000,https://r1eox.github.io"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
