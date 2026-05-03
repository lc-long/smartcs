from __future__ import annotations

import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.app.models.schemas import MessageRole
from backend.app.services.chat_history import get_chat_history_service

router = APIRouter(prefix="/api/v1/history", tags=["history"])


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    agent_name: str | None
    tools_called: list[str] | None
    created_at: str


class ConversationHistoryResponse(BaseModel):
    messages: list[MessageResponse]
    total: int


class ConversationListItem(BaseModel):
    id: str
    customer_id: str
    status: str
    last_message: str | None
    created_at: str
    updated_at: str


@router.get("/conversations/{conversation_id}")
async def get_conversation_history(
    conversation_id: str,
    limit: int = 50,
    offset: int = 0,
) -> ConversationHistoryResponse:
    service = get_chat_history_service()
    messages = await service.get_conversation_messages(conversation_id, limit, offset)

    return ConversationHistoryResponse(
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                agent_name=m.agent_name,
                tools_called=json.loads(m.tools_called) if m.tools_called else [],
                created_at=m.created_at.isoformat() if m.created_at else "",
            )
            for m in messages
        ],
        total=len(messages),
    )
