from __future__ import annotations

import asyncio
import threading
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger()

APPROVAL_KEY_PREFIX = "smartcs:approval:"


class ApprovalItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    conversation_id: str
    approval_type: str
    customer_id: str
    agent_name: str
    action_description: str
    action_params: dict = Field(default_factory=dict)
    risk_level: str = "medium"
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.now)
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    resolution_comment: str | None = None

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, data: str) -> ApprovalItem:
        return cls.model_validate_json(data)


class ApprovalQueue:
    """Approval queue with Redis persistence.

    Uses in-memory dict as cache, syncs to Redis for durability.
    """

    def __init__(self):
        self._queue: dict[str, ApprovalItem] = {}
        self._lock = threading.Lock()
        self._redis_client: Any = None
        self._initialized = False

    def _get_redis(self) -> Any:
        if self._redis_client is None:
            import redis.asyncio as redis

            from backend.app.core.config.settings import get_settings

            settings = get_settings()
            self._redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis_client

    async def _async_init(self) -> None:
        """Load pending approvals from Redis on startup."""
        if self._initialized:
            return
        try:
            client = self._get_redis()
            keys = await client.keys(f"{APPROVAL_KEY_PREFIX}*")
            for key in keys:
                data = await client.get(key)
                if data:
                    item = ApprovalItem.from_json(data)
                    if item.status == "pending":
                        self._queue[str(item.id)] = item
            self._initialized = True
            logger.info("approval_queue_loaded", count=len(self._queue))
        except Exception as e:
            logger.warning("approval_queue_load_failed", error=str(e))
            self._initialized = True

    def add(self, item: ApprovalItem) -> None:
        with self._lock:
            self._queue[str(item.id)] = item
        self._persist_background(item)
        logger.info(
            "approval_added",
            approval_id=str(item.id),
            type=item.approval_type,
            risk_level=item.risk_level,
        )

    def _persist_background(self, item: ApprovalItem) -> None:
        try:
            loop = asyncio.get_running_loop()
            if loop.is_closed():
                return
            task = loop.create_task(self._persist(item))
            task.add_done_callback(self._handle_persist_error_callback)
        except RuntimeError:
            return
        except Exception:
            return

    def _handle_persist_error_callback(self, task: asyncio.Task) -> None:
        try:
            if task.exc():
                logger.warning("approval_persist_failed", error=str(task.exc()))
        except Exception:
            pass

    async def _persist(self, item: ApprovalItem) -> None:
        try:
            client = self._get_redis()
            await client.set(
                f"{APPROVAL_KEY_PREFIX}{item.id}",
                item.to_json(),
                ex=86400 * 7,
            )
        except Exception as e:
            logger.warning("approval_persist_failed", approval_id=str(item.id), error=str(e))

    def get(self, approval_id: str) -> ApprovalItem | None:
        return self._queue.get(approval_id)

    def get_pending(self) -> list[ApprovalItem]:
        return [item for item in self._queue.values() if item.status == "pending"]

    def get_by_conversation(self, conversation_id: str) -> list[ApprovalItem]:
        return [item for item in self._queue.values() if item.conversation_id == conversation_id]

    def approve(self, approval_id: str, resolved_by: str, comment: str = "") -> ApprovalItem | None:
        with self._lock:
            item = self._queue.get(approval_id)
            if item and item.status == "pending":
                item.status = "approved"
                item.resolved_at = datetime.now()
                item.resolved_by = resolved_by
                item.resolution_comment = comment
                logger.info("approval_approved", approval_id=approval_id, by=resolved_by)
        self._persist_background(item)
        return item

    def reject(self, approval_id: str, resolved_by: str, comment: str = "") -> ApprovalItem | None:
        with self._lock:
            item = self._queue.get(approval_id)
            if item and item.status == "pending":
                item.status = "rejected"
                item.resolved_at = datetime.now()
                item.resolved_by = resolved_by
                item.resolution_comment = comment
                logger.info("approval_rejected", approval_id=approval_id, by=resolved_by)
        self._persist_background(item)
        return item

    def count_pending(self) -> int:
        return len(self.get_pending())


_approval_queue: ApprovalQueue | None = None


def get_approval_queue() -> ApprovalQueue:
    global _approval_queue
    if _approval_queue is None:
        _approval_queue = ApprovalQueue()
    return _approval_queue
