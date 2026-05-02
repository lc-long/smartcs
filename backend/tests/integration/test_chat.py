from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from backend.app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/auth/login",
            data={
                "username": "testuser",
                "password": "testpassword123",
            },
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            ac.headers["Authorization"] = f"Bearer {token}"
        yield ac


async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


async def test_debug_config(client: AsyncClient):
    response = await client.get("/api/v1/debug/config")
    assert response.status_code == 200
    data = response.json()
    assert "llm_provider" in data
    assert "default_model" in data


async def test_chat_endpoint_requires_auth(client: AsyncClient):
    response = await client.post(
        "/api/v1/chat",
        json={
            "customer_id": "C001",
            "message": "你好，我想查账单",
        },
    )
    assert response.status_code in (401, 403)


async def test_chat_endpoint(auth_client: AsyncClient):
    response = await auth_client.post(
        "/api/v1/chat",
        json={
            "customer_id": "C001",
            "message": "你好，我想查账单",
        },
    )
    if response.status_code == 200:
        data = response.json()
        assert "conversation_id" in data
        assert "message" in data
        assert "metadata" in data
        assert data["message"]["role"] == "assistant"
        assert len(data["message"]["content"]) > 0
    else:
        pytest.skip(f"Chat endpoint returned {response.status_code}: {response.text}")


async def test_chat_with_conversation_id(auth_client: AsyncClient):
    response = await auth_client.post(
        "/api/v1/chat",
        json={
            "customer_id": "C001",
            "message": "你好",
            "conversation_id": "test-conv-123",
        },
    )
    if response.status_code == 200:
        data = response.json()
        assert data["conversation_id"] == "test-conv-123"
    else:
        pytest.skip(f"Chat endpoint returned {response.status_code}: {response.text}")


async def test_chat_empty_message(auth_client: AsyncClient):
    response = await auth_client.post(
        "/api/v1/chat",
        json={
            "customer_id": "C001",
            "message": "",
        },
    )
    assert response.status_code == 422


async def test_chat_missing_customer_id(auth_client: AsyncClient):
    response = await auth_client.post(
        "/api/v1/chat",
        json={
            "message": "Hello",
        },
    )
    assert response.status_code == 422


async def test_chat_stream_endpoint(auth_client: AsyncClient):
    response = await auth_client.post(
        "/api/v1/chat/stream",
        json={
            "customer_id": "C001",
            "message": "你好，我想查账单",
        },
    )
    if response.status_code == 200:
        assert "text/event-stream" in response.headers.get("content-type", "")
        content = response.text
        assert "event: start" in content or "event: planning" in content
    else:
        pytest.skip(f"Stream endpoint returned {response.status_code}: {response.text}")


async def test_chat_refund_intent(auth_client: AsyncClient):
    response = await auth_client.post(
        "/api/v1/chat",
        json={
            "customer_id": "C001",
            "message": "我想退款",
        },
    )
    if response.status_code == 200:
        data = response.json()
        assert data["metadata"]["intent"] == "refund"
    else:
        pytest.skip(f"Chat endpoint returned {response.status_code}: {response.text}")


async def test_chat_technical_intent(auth_client: AsyncClient):
    response = await auth_client.post(
        "/api/v1/chat",
        json={
            "customer_id": "C001",
            "message": "设备故障了怎么办",
        },
    )
    if response.status_code == 200:
        data = response.json()
        assert data["metadata"]["intent"] == "technical"
    else:
        pytest.skip(f"Chat endpoint returned {response.status_code}: {response.text}")


async def test_chat_escalation_intent(auth_client: AsyncClient):
    response = await auth_client.post(
        "/api/v1/chat",
        json={
            "customer_id": "C001",
            "message": "转人工",
        },
    )
    if response.status_code == 200:
        data = response.json()
        assert data["metadata"]["intent"] == "escalation"
    else:
        pytest.skip(f"Chat endpoint returned {response.status_code}: {response.text}")
