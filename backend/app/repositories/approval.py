from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.db.conversation import Approval
from backend.app.repositories.base import BaseRepository


class ApprovalRepository(BaseRepository[Approval]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Approval)

    async def get_pending(self, limit: int = 50) -> list[Approval]:
        result = await self.session.execute(
            select(Approval)
            .where(Approval.status == "pending")
            .order_by(Approval.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_conversation(self, conversation_id: str) -> list[Approval]:
        result = await self.session.execute(
            select(Approval)
            .where(Approval.conversation_id == conversation_id)
            .order_by(Approval.created_at.desc())
        )
        return list(result.scalars().all())

    async def approve(
        self,
        approval_id: str,
        decided_by: str,
        comment: Optional[str] = None,
    ) -> Approval | None:
        return await self.update(
            approval_id,
            status="approved",
            decided_by=decided_by,
            decision_comment=comment,
            decided_at=datetime.now(),
        )

    async def reject(
        self,
        approval_id: str,
        decided_by: str,
        comment: Optional[str] = None,
    ) -> Approval | None:
        return await self.update(
            approval_id,
            status="rejected",
            decided_by=decided_by,
            decision_comment=comment,
            decided_at=datetime.now(),
        )

    async def create_approval(
        self,
        conversation_id: str,
        approval_type: str,
        customer_id: str,
        agent_name: str,
        action_description: str,
        action_params: Optional[dict] = None,
        risk_level: str = "medium",
    ) -> Approval:
        import json

        approval = Approval(
            conversation_id=conversation_id,
            approval_type=approval_type,
            customer_id=customer_id,
            agent_name=agent_name,
            action_description=action_description,
            action_params=json.dumps(action_params) if action_params else None,
            risk_level=risk_level,
        )
        return await self.create(approval)
