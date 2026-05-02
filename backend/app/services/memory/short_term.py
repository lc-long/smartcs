from __future__ import annotations

import json
import os
import threading
from pathlib import Path

import structlog
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from backend.app.services.redis.client import RedisCache

logger = structlog.get_logger()

MEMORY_BACKUP_DIR = Path("./memory_backups")
MEMORY_BACKUP_LOCK = threading.Lock()


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
    """Fallback in-memory store with file backup for development/testing."""

    def __init__(self, max_messages_per_session: int = 50):
        self._sessions: dict[str, list[dict]] = {}
        self._max_messages = max_messages_per_session
        self._backup_dir = MEMORY_BACKUP_DIR
        self._backup_dir.mkdir(exist_ok=True, parents=True)
        self._lock = threading.Lock()
        self._load_from_backup()

    def _get_backup_path(self, session_id: str) -> Path:
        return self._backup_dir / f"{session_id}.json"

    def _load_from_backup(self) -> None:
        """Load sessions from backup files on startup"""
        try:
            for backup_file in self._backup_dir.glob("*.json"):
                session_id = backup_file.stem
                try:
                    with open(backup_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            self._sessions[session_id] = data
                            logger.info("memory_backup_loaded", session_id=session_id, count=len(data))
                except Exception as e:
                    logger.warning("memory_backup_load_failed", session_id=session_id, error=str(e))
        except Exception as e:
            logger.warning("memory_backup_dir_read_failed", error=str(e))

    def _save_to_backup(self, session_id: str) -> None:
        """Save session to backup file"""
        try:
            messages = self._sessions.get(session_id, [])
            backup_path = self._get_backup_path(session_id)
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(messages, f, ensure_ascii=False)
        except Exception as e:
            logger.warning("memory_backup_save_failed", session_id=session_id, error=str(e))

    def _delete_backup(self, session_id: str) -> None:
        """Delete backup file for session"""
        try:
            backup_path = self._get_backup_path(session_id)
            if backup_path.exists():
                backup_path.unlink()
        except Exception as e:
            logger.warning("memory_backup_delete_failed", session_id=session_id, error=str(e))

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

        with self._lock:
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

        self._save_to_backup(session_id)

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
        with self._lock:
            self._sessions.pop(session_id, None)
        self._delete_backup(session_id)

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
            logger.warning("fallback_to_in_memory_store_with_backup")
    return _short_term_store