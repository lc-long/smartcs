from __future__ import annotations

import os
import pytest
from httpx import AsyncClient, ASGITransport

os.environ["APP_ENV"] = "development"
os.environ["DEBUG"] = "true"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"


@pytest.fixture
async def client():
    from backend.app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def authenticated_client():
    from backend.app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/auth/login",
            data={
                "username": "agent1",
                "password": "agent123",
            },
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            ac.headers["Authorization"] = f"Bearer {token}"
        yield ac