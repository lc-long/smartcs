from __future__ import annotations

import json

import structlog
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from backend.app.services.redis.client import RedisCache

logger = structlog.get_logger()


class RedisMemoryStore:
    """Redis-based memory store for conversation history."""

    def __init__(self, max_messages_per_session: int = 50):
        self.cache = RedisCache(prefix="smartcs:memory")
        self._max_messages = max_messages_per_session

    async def add_message(
        self,
        session_id: str,
        message: BaseMessage,
        agent_name: str | None = None,
    ) -> None:
        role = "user" if isinstance(message, HumanMessage) else "assistant"
        content = (
            message.content
            if isinstance(message.content, str)
            else str(message.content)
        )

        msg_data = {
            "role": role,
            "content": content,
            "agent_name": agent_name,
        }

        messages = await self.get_messages(session_id)
        messages.append(msg_data)

        if len(messages) > self._max_messages:
            messages = messages[-self._max_messages :]

        await self.cache.set_json(session_id, messages, expire=86400)

    async def get_messages(
        self,
        session_id: str,
        limit: int | None = None,
    ) -> list[dict]:
        messages = await self.cache.get_json(session_id)
        if messages is None:
            return []
        if limit:
            return messages[-limit:]
        return messages

    async def clear_session(self, session_id: str) -> None:
        await self.cache.delete(session_id)

    async def get_session_ids(self) -> list[str]:
        keys = await self.cache.keys("*")
        return [key.split(":")[-1] for key in keys]


class InMemoryStore:
    """Fallback in-memory store for development/testing."""

    def __init__(self, max_messages_per_session: int = 50):
        self._sessions: dict[str, list[dict]] = {}
        self._max_messages = max_messages_per_session

    async def add_message(
        self,
        session_id: str,
        message: BaseMessage,
        agent_name: str | None = None,
    ) -> None:
        if session_id not in self._sessions:
            self._sessions[session_id] = []

        role = "user" if isinstance(message, HumanMessage) else "assistant"
        content = (
            message.content
            if isinstance(message.content, str)
            else str(message.content)
        )

        self._sessions[session_id].append(
            {
                "role": role,
                "content": content,
                "agent_name": agent_name,
            }
        )

        if len(self._sessions[session_id]) > self._max_messages:
            self._sessions[session_id] = self._sessions[session_id][
                -self._max_messages :
            ]

    async def get_messages(
        self,
        session_id: str,
        limit: int | None = None,
    ) -> list[dict]:
        messages = self._sessions.get(session_id, [])
        if limit:
            return messages[-limit:]
        return messages

    async def clear_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    async def get_session_ids(self) -> list[str]:
        return list(self._sessions.keys())


_short_term_store = None


def get_short_term_memory():
    global _short_term_store
    if _short_term_store is None:
        try:
            _short_term_store = RedisMemoryStore()
            logger.info("using_redis_memory_store")
        except Exception:
            _short_term_store = InMemoryStore()
            logger.warning("fallback_to_in_memory_store")
    return _short_term_store
