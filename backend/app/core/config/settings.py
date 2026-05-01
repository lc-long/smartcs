from __future__ import annotations

from enum import Enum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnvironment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "SmartCS"
    app_env: AppEnvironment = AppEnvironment.DEVELOPMENT
    debug: bool = True
    log_level: str = "INFO"

    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000"]

    # Database
    database_url: str = "postgresql+asyncpg://smartcs:smartcs@localhost:5432/smartcs"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # LLM API Keys
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    anthropic_api_key: str = ""

    # Model Configuration
    default_model: str = "gpt-4o-mini"
    router_model: str = "gpt-4o-mini"
    billing_model: str = "gpt-4o"
    technical_model: str = "gpt-4o"
    refund_model: str = "gpt-4o"
    general_model: str = "gpt-4o-mini"

    # Vector Database
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection: str = "knowledge_base"

    # Security
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Observability
    enable_tracing: bool = True
    trace_sample_rate: float = 1.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
