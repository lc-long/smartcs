from __future__ import annotations

import json
from typing import Any, Optional

import redis.asyncio as redis
import structlog

from backend.app.core.config.settings import get_settings

logger = structlog.get_logger()

_redis_client: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        logger.info("redis_connected", url=settings.redis_url)
    return _redis_client


async def close_redis():
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("redis_closed")


class RedisCache:
    def __init__(self, prefix: str = "smartcs"):
        self.prefix = prefix

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Optional[str]:
        client = await get_redis()
        return await client.get(self._key(key))

    async def set(
        self,
        key: str,
        value: str,
        expire: int = 3600,
    ) -> None:
        client = await get_redis()
        await client.set(self._key(key), value, ex=expire)

    async def delete(self, key: str) -> None:
        client = await get_redis()
        await client.delete(self._key(key))

    async def get_json(self, key: str) -> Optional[Any]:
        data = await self.get(key)
        if data:
            return json.loads(data)
        return None

    async def set_json(
        self,
        key: str,
        value: Any,
        expire: int = 3600,
    ) -> None:
        await self.set(key, json.dumps(value), expire)

    async def exists(self, key: str) -> bool:
        client = await get_redis()
        return await client.exists(self._key(key))

    async def keys(self, pattern: str) -> list[str]:
        client = await get_redis()
        return await client.keys(self._key(pattern))

    async def incr(self, key: str) -> int:
        client = await get_redis()
        return await client.incr(self._key(key))

    async def expire(self, key: str, seconds: int) -> None:
        client = await get_redis()
        await client.expire(self._key(key), seconds)


class RedisSessionStore:
    """Redis-based session store for conversation context."""

    def __init__(self):
        self.cache = RedisCache(prefix="smartcs:session")

    async def get_session(self, conversation_id: str) -> Optional[dict]:
        return await self.cache.get_json(conversation_id)

    async def save_session(
        self,
        conversation_id: str,
        data: dict,
        expire: int = 86400,
    ) -> None:
        await self.cache.set_json(conversation_id, data, expire)

    async def delete_session(self, conversation_id: str) -> None:
        await self.cache.delete(conversation_id)

    async def update_session(
        self,
        conversation_id: str,
        updates: dict,
    ) -> None:
        session = await self.get_session(conversation_id)
        if session:
            session.update(updates)
            await self.save_session(conversation_id, session)


class LangGraphCheckpointer:
    """Redis-based checkpointer for LangGraph state persistence."""

    def __init__(self):
        self.cache = RedisCache(prefix="smartcs:checkpoint")

    async def get_state(self, thread_id: str) -> Optional[dict]:
        return await self.cache.get_json(thread_id)

    async def save_state(
        self,
        thread_id: str,
        state: dict,
        expire: int = 86400,
    ) -> None:
        await self.cache.set_json(thread_id, state, expire)

    async def delete_state(self, thread_id: str) -> None:
        await self.cache.delete(thread_id)

    async def list_threads(self, pattern: str = "*") -> list[str]:
        return await self.cache.keys(pattern)
