from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger()


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


class ApprovalQueue:
    """In-memory approval queue for development/testing.
    In production, use ApprovalRepository with PostgreSQL.
    """

    def __init__(self):
        self._queue: dict[str, ApprovalItem] = {}

    def add(self, item: ApprovalItem) -> None:
        self._queue[str(item.id)] = item
        logger.info(
            "approval_added",
            approval_id=str(item.id),
            type=item.approval_type,
            risk_level=item.risk_level,
        )

    def get(self, approval_id: str) -> ApprovalItem | None:
        return self._queue.get(approval_id)

    def get_pending(self) -> list[ApprovalItem]:
        return [item for item in self._queue.values() if item.status == "pending"]

    def get_by_conversation(self, conversation_id: str) -> list[ApprovalItem]:
        return [
            item for item in self._queue.values()
            if item.conversation_id == conversation_id
        ]

    def approve(self, approval_id: str, resolved_by: str, comment: str = "") -> ApprovalItem | None:
        item = self._queue.get(approval_id)
        if item and item.status == "pending":
            item.status = "approved"
            item.resolved_at = datetime.now()
            item.resolved_by = resolved_by
            item.resolution_comment = comment
            logger.info("approval_approved", approval_id=approval_id, by=resolved_by)
            return item
        return None

    def reject(self, approval_id: str, resolved_by: str, comment: str = "") -> ApprovalItem | None:
        item = self._queue.get(approval_id)
        if item and item.status == "pending":
            item.status = "rejected"
            item.resolved_at = datetime.now()
            item.resolved_by = resolved_by
            item.resolution_comment = comment
            logger.info("approval_rejected", approval_id=approval_id, by=resolved_by)
            return item
        return None

    def count_pending(self) -> int:
        return len(self.get_pending())


_approval_queue: ApprovalQueue | None = None


def get_approval_queue() -> ApprovalQueue:
    global _approval_queue
    if _approval_queue is None:
        _approval_queue = ApprovalQueue()
    return _approval_queue
