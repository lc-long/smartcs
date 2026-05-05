from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.app.api.v1.auth import get_current_user
from backend.app.models.db.user import User
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
    is_deleted: bool


@router.get("/conversations")
async def get_user_conversations(
    include_deleted: bool = False,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
) -> list[ConversationListItem]:
    """Get user's own conversations"""
    service = get_chat_history_service()
    # Regular users can only see their own conversations
    if current_user.role == "viewer":
        customer_id = current_user.customer_id
        if not customer_id:
            return []
        conversations = await service.get_user_conversations(
            customer_id=customer_id,
            include_deleted=include_deleted,
            limit=limit,
            offset=offset,
        )
    else:
        # Admin/agent can see all conversations
        conversations = await service.get_all_conversations_for_admin(
            include_deleted=True,
            limit=limit,
            offset=offset,
        )

    return [
        ConversationListItem(
            id=c.id,
            customer_id=c.customer_id,
            status=c.status,
            last_message=c.last_message,
            created_at=c.created_at.isoformat() if c.created_at else "",
            updated_at=c.updated_at.isoformat() if c.updated_at else "",
            is_deleted=c.is_deleted or False,
        )
        for c in conversations
    ]


@router.get("/conversations/{conversation_id}")
async def get_conversation_history(
    conversation_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
) -> ConversationHistoryResponse:
    """Get conversation messages with access control"""
    service = get_chat_history_service()

    # First check if user has access to this conversation
    conversations = await service.get_user_conversations(
        customer_id=current_user.customer_id or "",
        include_deleted=True,  # Include deleted for access check
    )
    conv_ids = [c.id for c in conversations]

    # Admin/agent can view any conversation, regular users only their own
    if current_user.role == "viewer" and conversation_id not in conv_ids:
        raise HTTPException(status_code=403, detail="Access denied")

    messages = await service.get_conversation_messages(
        conversation_id, limit, offset, include_deleted=True
    )

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


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Soft delete a conversation (user can only delete their own)"""
    service = get_chat_history_service()

    # Only regular users can delete conversations
    if current_user.role != "viewer":
        raise HTTPException(
            status_code=403,
            detail="Only customers can delete their own conversations"
        )

    customer_id = current_user.customer_id
    if not customer_id:
        raise HTTPException(status_code=400, detail="No customer ID associated with this user")

    success = await service.soft_delete_conversation(conversation_id, customer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found or access denied")

    return {"message": "Conversation deleted successfully", "conversation_id": conversation_id}


@router.post("/conversations/{conversation_id}/restore")
async def restore_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Restore a soft-deleted conversation (admin only)"""
    # Only admin can restore conversations
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    service = get_chat_history_service()
    success = await service.restore_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found or not deleted")

    return {"message": "Conversation restored successfully", "conversation_id": conversation_id}
