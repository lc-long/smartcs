from __future__ import annotations

import json
import time
from uuid import UUID, uuid4

import structlog
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from backend.app.api.v1.auth import get_current_user
from backend.app.models.db.user import User
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
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    start_time = time.time()

    # 数据隔离：普通用户只能访问自己的数据
    if current_user.role == "viewer":
        if current_user.customer_id and request.customer_id != current_user.customer_id:
            raise HTTPException(
                status_code=403,
                detail="You can only access your own data",
            )
        # 强制使用用户关联的客户ID
        customer_id = current_user.customer_id or request.customer_id
    else:
        # 管理员和客服可以访问任何客户的数据
        customer_id = request.customer_id

    conversation_id = request.conversation_id or uuid4()
    logger.info(
        "chat_request",
        conversation_id=str(conversation_id),
        customer_id=customer_id,
        user_id=current_user.id,
        user_role=current_user.role,
    )

    messages = [HumanMessage(content=request.message)]

    workflow = get_workflow()
    result = await workflow.run(
        messages=messages,
        conversation_id=str(conversation_id),
        customer_id=customer_id,
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


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    conversation_id = request.conversation_id or uuid4()

    async def event_generator():
        start_time = time.time()

        yield _sse_event(
            "start",
            {
                "conversation_id": str(conversation_id),
                "customer_id": request.customer_id,
            },
        )

        messages = [HumanMessage(content=request.message)]
        workflow = get_workflow()

        try:
            yield _sse_event("processing", {"status": "routing"})

            result = await workflow.run(
                messages=messages,
                conversation_id=str(conversation_id),
                customer_id=request.customer_id,
            )

            yield _sse_event(
                "routing",
                {
                    "intent": result["current_intent"],
                    "confidence": result["routing_confidence"],
                    "reasoning": result["routing_reasoning"],
                    "agent": result["active_agent"],
                },
            )

            yield _sse_event("processing", {"status": "generating"})

            response_text = result["agent_response"]
            chunk_size = 20
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i : i + chunk_size]
                yield _sse_event("chunk", {"content": chunk})

            latency_ms = int((time.time() - start_time) * 1000)

            yield _sse_event(
                "complete",
                {
                    "conversation_id": str(conversation_id),
                    "agent": result["active_agent"],
                    "intent": result["current_intent"],
                    "tools_called": result["tools_called"],
                    "latency_ms": latency_ms,
                },
            )

        except Exception as e:
            logger.exception("chat_stream_error")
            yield _sse_event(
                "error",
                {"message": "处理请求时出现错误，请稍后重试"},
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
