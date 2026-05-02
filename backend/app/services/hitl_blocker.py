from __future__ import annotations

import asyncio
import threading

import structlog

from backend.app.services.redis.client import get_redis

logger = structlog.get_logger()

HITL_CHANNEL_PREFIX = "smartcs:hitl:"


class HITLBlocker:
    """Manages blocking wait for HITL approvals using asyncio.Event + Redis pub/sub."""

    def __init__(self):
        self._events: dict[str, asyncio.Event] = {}
        self._lock = threading.Lock()
        self._pubsub_tasks: dict[str, asyncio.Task] = {}
        self._initialized = False

    def _get_event(self, approval_id: str) -> asyncio.Event:
        with self._lock:
            if approval_id not in self._events:
                self._events[approval_id] = asyncio.Event()
            return self._events[approval_id]

    async def wait_for_approval(
        self,
        approval_id: str,
        timeout_seconds: float = 86400,
    ) -> str | None:
        """Wait for approval decision. Returns 'approved', 'rejected', or None on timeout."""
        event = self._get_event(approval_id)
        channel = f"{HITL_CHANNEL_PREFIX}{approval_id}"

        async def listen_redis():
            try:
                redis_client = await get_redis()
                pubsub = redis_client.pubsub()
                await pubsub.subscribe(channel)
                logger.info("hitl_subscribed", channel=channel)

                async for message in pubsub.listen():
                    if message["type"] == "message":
                        data = message["data"]
                        logger.info("hitl_redis_message", channel=channel, data=data)
                        if data in ("approved", "rejected"):
                            event.set()
                            break
            except Exception as e:
                logger.warning("hitl_redis_listen_error", error=str(e))
                event.set()
            finally:
                try:
                    await pubsub.unsubscribe(channel)
                    await pubsub.close()
                except Exception:
                    pass

        listen_task = asyncio.create_task(listen_redis())

        try:
            logger.info("hitl_waiting", approval_id=approval_id, timeout=timeout_seconds)
            try:
                await asyncio.wait_for(event.wait(), timeout=timeout_seconds)
            except TimeoutError:
                logger.info("hitl_timeout", approval_id=approval_id)
                return None

            result = await self._get_result(approval_id)
            return result
        finally:
            listen_task.cancel()
            try:
                await listen_task
            except asyncio.CancelledError:
                pass
            self._cleanup(approval_id)

    async def _get_result(self, approval_id: str) -> str | None:
        from backend.app.services.approval_queue import get_approval_queue

        queue = get_approval_queue()
        item = queue.get(approval_id)
        if item:
            return item.status
        return None

    def notify(self, approval_id: str, decision: str) -> None:
        """Notify waiting workflow that approval decision was made."""
        event = self._events.get(approval_id)
        if event and not event.is_set():
            logger.info("hitl_notify", approval_id=approval_id, decision=decision)
            event.set()

    def _cleanup(self, approval_id: str) -> None:
        with self._lock:
            self._events.pop(approval_id, None)
            task = self._pubsub_tasks.pop(approval_id, None)
            if task and not task.done():
                task.cancel()


_hitl_blocker: HITLBlocker | None = None


def get_hitl_blocker() -> HITLBlocker:
    global _hitl_blocker
    if _hitl_blocker is None:
        _hitl_blocker = HITLBlocker()
    return _hitl_blocker
