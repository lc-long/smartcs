from __future__ import annotations

import os

import pytest

os.environ["APP_ENV"] = "development"
os.environ["DEBUG"] = "true"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://smartcs:smartcs@localhost:5432/smartcs"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
