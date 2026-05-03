from __future__ import annotations

import json
import structlog
from datetime import datetime
from typing import Any

from backend.app.core.database import get_session_factory
from backend.app.models.db.conversation import Conversation, Message

logger = structlog.get_logger()


class ChatHistoryService:
    def __init__(self):
        self._session_factory = None

    def _get_session_factory(self):
        if self._session_factory is None:
            self._session_factory = get_session_factory()
        return self._session_factory

    async def save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        agent_name: str | None = None,
        tools_called: list[str] | None = None,
        token_usage: dict | None = None,
    ) -> Message:
        factory = self._get_session_factory()
        async with factory() as session:
            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                agent_name=agent_name,
                tools_called=json.dumps(tools_called) if tools_called else None,
                token_usage=json.dumps(token_usage) if token_usage else None,
            )
            session.add(message)

            # Update conversation last_message
            from sqlalchemy import select
            result = await session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            if conversation:
                conversation.last_message = content[:500]
                conversation.updated_at = datetime.now()

            await session.commit()
            logger.info("message_saved", conversation_id=conversation_id, role=role)
            return message

    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Message]:
        factory = self._get_session_factory()
        async with factory() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            messages = list(result.scalars().all())
            return list(reversed(messages))

    async def create_conversation(
        self,
        conversation_id: str,
        customer_id: str,
        metadata: dict | None = None,
    ) -> Conversation:
        factory = self._get_session_factory()
        async with factory() as session:
            conversation = Conversation(
                id=conversation_id,
                customer_id=customer_id,
                status="active",
                metadata_json=json.dumps(metadata) if metadata else None,
            )
            session.add(conversation)
            await session.commit()
            logger.info("conversation_created", conversation_id=conversation_id)
            return conversation

    async def end_conversation(self, conversation_id: str) -> None:
        factory = self._get_session_factory()
        async with factory() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            if conversation:
                conversation.status = "ended"
                conversation.updated_at = datetime.now()
                await session.commit()
                logger.info("conversation_ended", conversation_id=conversation_id)


_chat_history_service: ChatHistoryService | None = None


def get_chat_history_service() -> ChatHistoryService:
    global _chat_history_service
    if _chat_history_service is None:
        _chat_history_service = ChatHistoryService()
    return _chat_history_service
