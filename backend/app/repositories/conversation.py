from __future__ import annotations

import json

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.db.conversation import Conversation, Message
from backend.app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Conversation)

    async def get_by_customer(
        self,
        customer_id: str,
        status: str | None = None,
        limit: int = 50,
        include_deleted: bool = False,
    ) -> list[Conversation]:
        query = select(Conversation).where(Conversation.customer_id == customer_id)
        if not include_deleted:
            query = query.where(~Conversation.is_deleted)
        if status:
            query = query.where(Conversation.status == status)
        query = query.order_by(Conversation.updated_at.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active_conversation(
        self,
        customer_id: str,
        include_deleted: bool = False,
    ) -> Conversation | None:
        stmt = (
            select(Conversation)
            .where(Conversation.customer_id == customer_id)
            .where(Conversation.status == "active")
        )
        if not include_deleted:
            stmt = stmt.where(~Conversation.is_deleted)
        stmt = stmt.order_by(Conversation.updated_at.desc()).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(self, conversation_id: str, status: str) -> Conversation | None:
        return await self.update(conversation_id, status=status)

    async def update_last_message(self, conversation_id: str, message: str) -> None:
        await self.update(conversation_id, last_message=message[:500])

    async def update_active_agent(self, conversation_id: str, agent_name: str) -> None:
        await self.update(conversation_id, active_agent=agent_name)

    async def get_escalated_conversations(
        self,
        include_deleted: bool = False,
        limit: int = 50,
    ) -> list[Conversation]:
        """Get conversations escalated to human agents"""
        stmt = (
            select(Conversation)
            .where(Conversation.status.in_(["escalated", "human_handling"]))
        )
        if not include_deleted:
            stmt = stmt.where(~Conversation.is_deleted)
        stmt = stmt.order_by(Conversation.updated_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_for_admin(
        self,
        include_deleted: bool = True,
        status: str | None = None,
        customer_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Conversation]:
        """Get all conversations for admin (includes deleted by default)"""
        stmt = select(Conversation)
        if not include_deleted:
            stmt = stmt.where(~Conversation.is_deleted)
        if status:
            stmt = stmt.where(Conversation.status == status)
        if customer_id:
            stmt = stmt.where(Conversation.customer_id == customer_id)
        stmt = stmt.order_by(Conversation.updated_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class MessageRepository(BaseRepository[Message]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Message)

    async def get_by_conversation(
        self,
        conversation_id: str,
        limit: int = 100,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
        )
        if not include_deleted:
            stmt = stmt.where(~Message.is_deleted)
        stmt = stmt.order_by(Message.created_at.asc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_conversation_message_count(
        self,
        conversation_id: str,
        include_deleted: bool = False,
    ) -> int:
        stmt = select(func.count(Message.id)).where(
            Message.conversation_id == conversation_id
        )
        if not include_deleted:
            stmt = stmt.where(~Message.is_deleted)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_last_message(
        self,
        conversation_id: str,
        include_deleted: bool = False,
    ) -> Message | None:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
        )
        if not include_deleted:
            stmt = stmt.where(~Message.is_deleted)
        stmt = stmt.order_by(Message.created_at.desc()).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        agent_name: str | None = None,
        tools_called: list[str] | None = None,
        token_usage: dict | None = None,
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
