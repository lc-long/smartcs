from __future__ import annotations

import json
from datetime import datetime

import structlog

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
        include_deleted: bool = False,
    ) -> list[Message]:
        factory = self._get_session_factory()
        async with factory() as session:
            from sqlalchemy import select
            stmt = (
                select(Message)
                .where(Message.conversation_id == conversation_id)
            )
            if not include_deleted:
                stmt = stmt.where(~Message.is_deleted)
            stmt = stmt.order_by(Message.created_at.desc()).limit(limit).offset(offset)
            result = await session.execute(stmt)
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

    async def soft_delete_conversation(
        self,
        conversation_id: str,
        deleted_by: str,
    ) -> bool:
        """Soft delete a conversation and its messages (user only)"""
        factory = self._get_session_factory()
        async with factory() as session:
            from sqlalchemy import select, update

            # Check if conversation exists and is not already deleted
            result = await session.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    ~Conversation.is_deleted,
                )
            )
            conversation = result.scalar_one_or_none()
            if not conversation:
                logger.warning(
                    "conversation_not_found_or_already_deleted",
                    conversation_id=conversation_id,
                )
                return False

            # Only the customer who owns the conversation can delete it
            if conversation.customer_id != deleted_by:
                logger.warning(
                    "unauthorized_delete_attempt",
                    conversation_id=conversation_id,
                    deleted_by=deleted_by,
                )
                return False

            now = datetime.now()

            # Soft delete conversation
            await session.execute(
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(is_deleted=True, deleted_at=now, deleted_by=deleted_by)
            )

            # Soft delete all messages in this conversation
            await session.execute(
                update(Message)
                .where(Message.conversation_id == conversation_id)
                .values(is_deleted=True, deleted_at=now, deleted_by=deleted_by)
            )

            await session.commit()
            logger.info(
                "conversation_soft_deleted",
                conversation_id=conversation_id,
                deleted_by=deleted_by,
            )
            return True

    async def restore_conversation(
        self,
        conversation_id: str,
    ) -> bool:
        """Restore a soft-deleted conversation (admin only)"""
        factory = self._get_session_factory()
        async with factory() as session:
            from sqlalchemy import select, update

            # Check if conversation exists and is deleted
            result = await session.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.is_deleted,
                )
            )
            conversation = result.scalar_one_or_none()
            if not conversation:
                logger.warning(
                    "conversation_not_found_or_not_deleted",
                    conversation_id=conversation_id,
                )
                return False

            # Restore conversation
            await session.execute(
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(is_deleted=False, deleted_at=None, deleted_by=None)
            )

            # Restore all messages in this conversation
            await session.execute(
                update(Message)
                .where(Message.conversation_id == conversation_id)
                .values(is_deleted=False, deleted_at=None, deleted_by=None)
            )

            await session.commit()
            logger.info("conversation_restored", conversation_id=conversation_id)
            return True

    async def get_user_conversations(
        self,
        customer_id: str,
        include_deleted: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Conversation]:
        """Get conversations for a specific user"""
        factory = self._get_session_factory()
        async with factory() as session:
            from sqlalchemy import select
            stmt = (
                select(Conversation)
                .where(Conversation.customer_id == customer_id)
            )
            if not include_deleted:
                stmt = stmt.where(~Conversation.is_deleted)
            stmt = stmt.order_by(Conversation.updated_at.desc()).limit(limit).offset(offset)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_escalated_conversations(
        self,
        include_deleted: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Conversation]:
        """Get conversations that were escalated to human agents"""
        factory = self._get_session_factory()
        async with factory() as session:
            from sqlalchemy import select
            stmt = (
                select(Conversation)
                .where(Conversation.status.in_(["escalated", "human_handling"]))
            )
            if not include_deleted:
                stmt = stmt.where(~Conversation.is_deleted)
            stmt = stmt.order_by(Conversation.updated_at.desc()).limit(limit).offset(offset)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_all_conversations_for_admin(
        self,
        include_deleted: bool = True,
        status: str | None = None,
        customer_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Conversation]:
        """Get all conversations for admin (includes deleted by default)"""
        factory = self._get_session_factory()
        async with factory() as session:
            from sqlalchemy import select
            stmt = select(Conversation)
            if not include_deleted:
                stmt = stmt.where(~Conversation.is_deleted)
            if status:
                stmt = stmt.where(Conversation.status == status)
            if customer_id:
                stmt = stmt.where(Conversation.customer_id == customer_id)
            stmt = stmt.order_by(Conversation.updated_at.desc()).limit(limit).offset(offset)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def permanent_delete_conversation(
        self,
        conversation_id: str,
    ) -> bool:
        """Permanently delete a conversation and its messages"""
        factory = self._get_session_factory()
        async with factory() as session:
            from sqlalchemy import delete, select

            # Check if conversation exists
            result = await session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            if not conversation:
                return False

            # Delete all messages
            await session.execute(
                delete(Message).where(Message.conversation_id == conversation_id)
            )

            # Delete conversation
            await session.execute(
                delete(Conversation).where(Conversation.id == conversation_id)
            )

            await session.commit()
            logger.info("conversation_permanently_deleted", conversation_id=conversation_id)
            return True


_chat_history_service: ChatHistoryService | None = None


def get_chat_history_service() -> ChatHistoryService:
    global _chat_history_service
    if _chat_history_service is None:
        _chat_history_service = ChatHistoryService()
    return _chat_history_service
