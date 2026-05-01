from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from backend.app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
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


async def test_chat_endpoint(client: AsyncClient):
    response = await client.post(
        "/api/v1/chat",
        json={
            "customer_id": "test-customer",
            "message": "你好，我想查账单",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert "message" in data
    assert "metadata" in data
    assert data["message"]["role"] == "assistant"
    assert len(data["message"]["content"]) > 0


async def test_chat_with_conversation_id(client: AsyncClient):
    response = await client.post(
        "/api/v1/chat",
        json={
            "customer_id": "test-customer",
            "message": "你好",
            "conversation_id": "test-conv-123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"] == "test-conv-123"


async def test_chat_empty_message(client: AsyncClient):
    response = await client.post(
        "/api/v1/chat",
        json={
            "customer_id": "test-customer",
            "message": "",
        },
    )
    assert response.status_code == 422


async def test_chat_missing_customer_id(client: AsyncClient):
    response = await client.post(
        "/api/v1/chat",
        json={
            "message": "Hello",
        },
    )
    assert response.status_code == 422


async def test_chat_stream_endpoint(client: AsyncClient):
    response = await client.post(
        "/api/v1/chat/stream",
        json={
            "customer_id": "test-customer",
            "message": "你好，我想查账单",
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    content = response.text
    assert "event: start" in content
    assert "event: routing" in content
    assert "event: complete" in content


async def test_chat_refund_intent(client: AsyncClient):
    response = await client.post(
        "/api/v1/chat",
        json={
            "customer_id": "test-customer",
            "message": "我想退款",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["intent"] == "refund"


async def test_chat_technical_intent(client: AsyncClient):
    response = await client.post(
        "/api/v1/chat",
        json={
            "customer_id": "test-customer",
            "message": "设备故障了怎么办",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["intent"] == "technical"


async def test_chat_escalation_intent(client: AsyncClient):
    response = await client.post(
        "/api/v1/chat",
        json={
            "customer_id": "test-customer",
            "message": "转人工",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["intent"] == "escalation"
