from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.db.conversation import Conversation, Message
from backend.app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Conversation)

    async def get_by_customer(
        self,
        customer_id: str,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> list[Conversation]:
        query = select(Conversation).where(Conversation.customer_id == customer_id)
        if status:
            query = query.where(Conversation.status == status)
        query = query.order_by(Conversation.updated_at.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active_conversation(self, customer_id: str) -> Conversation | None:
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.customer_id == customer_id)
            .where(Conversation.status == "active")
            .order_by(Conversation.updated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update_status(self, conversation_id: str, status: str) -> Conversation | None:
        return await self.update(conversation_id, status=status)

    async def update_last_message(self, conversation_id: str, message: str) -> None:
        await self.update(conversation_id, last_message=message[:500])

    async def update_active_agent(self, conversation_id: str, agent_name: str) -> None:
        await self.update(conversation_id, active_agent=agent_name)


class MessageRepository(BaseRepository[Message]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Message)

    async def get_by_conversation(
        self,
        conversation_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Message]:
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_conversation_message_count(self, conversation_id: str) -> int:
        result = await self.session.execute(
            select(func.count(Message.id))
            .where(Message.conversation_id == conversation_id)
        )
        return result.scalar() or 0

    async def get_last_message(self, conversation_id: str) -> Message | None:
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        agent_name: Optional[str] = None,
        tools_called: Optional[list[str]] = None,
        token_usage: Optional[dict] = None,
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            agent_name=agent_name,
            tools_called=json.dumps(tools_called) if tools_called else None,
            token_usage=json.dumps(token_usage) if token_usage else None,
        )
        return await self.create(msg)
