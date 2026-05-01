from __future__ import annotations

import time
from uuid import UUID, uuid4

import structlog
from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage

from backend.app.models.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatResponseMetadata,
    MessageRole,
)
from backend.app.workflows.customer_service import get_workflow

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    start_time = time.time()

    conversation_id = request.conversation_id or uuid4()
    logger.info(
        "chat_request",
        conversation_id=str(conversation_id),
        customer_id=request.customer_id,
    )

    messages = [HumanMessage(content=request.message)]

    workflow = get_workflow()
    result = await workflow.run(
        messages=messages,
        conversation_id=str(conversation_id),
        customer_id=request.customer_id,
    )

    latency_ms = int((time.time() - start_time) * 1000)

    response_message = ChatMessage(
        id=uuid4(),
        role=MessageRole.ASSISTANT,
        content=result["agent_response"],
        agent_name=result["active_agent"],
        tools_called=result["tools_called"],
    )

    metadata = ChatResponseMetadata(
        intent=result["current_intent"],
        confidence=result["routing_confidence"],
        routing_reasoning=result["routing_reasoning"],
        model_used=result["active_agent"],
        token_usage=result["token_usage"],
        latency_ms=latency_ms,
    )

    logger.info(
        "chat_response",
        conversation_id=str(conversation_id),
        agent=result["active_agent"],
        latency_ms=latency_ms,
    )

    return ChatResponse(
        conversation_id=conversation_id,
        message=response_message,
        metadata=metadata,
    )
