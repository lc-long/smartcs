from __future__ import annotations

import os

import pytest

os.environ["APP_ENV"] = "development"
os.environ["DEBUG"] = "true"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["JWT_SECRET_KEY"] = "test-secret"
