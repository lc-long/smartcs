from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.services.approval_queue import ApprovalItem, get_approval_queue
from backend.app.api.websocket.chat_ws import manager

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class ApprovalDecisionRequest(BaseModel):
    decision: str
    comment: str = ""


class TakeoverRequest(BaseModel):
    agent_id: str
    reason: str = ""


@router.get("/approvals")
async def list_pending_approvals() -> dict:
    queue = get_approval_queue()
    pending = queue.get_pending()
    return {
        "items": [item.model_dump() for item in pending],
        "total": len(pending),
    }


@router.get("/approvals/{approval_id}")
async def get_approval(approval_id: str) -> dict:
    queue = get_approval_queue()
    item = queue.get(approval_id)
    if not item:
        raise HTTPException(status_code=404, detail="Approval not found")
    return item.model_dump()


@router.post("/approvals/{approval_id}")
async def decide_approval(approval_id: str, request: ApprovalDecisionRequest) -> dict:
    queue = get_approval_queue()

    if request.decision == "approve":
        item = queue.approve(approval_id, resolved_by="admin", comment=request.comment)
    elif request.decision == "reject":
        item = queue.reject(approval_id, resolved_by="admin", comment=request.comment)
    else:
        raise HTTPException(status_code=400, detail="Decision must be 'approve' or 'reject'")

    if not item:
        raise HTTPException(status_code=404, detail="Approval not found or already resolved")

    # 如果是退款审批，需要更新Refund记录状态
    if item.approval_type == "refund_approval":
        from backend.app.models.db.ecommerce import Refund
        from backend.app.core.database import get_session_factory
        from sqlalchemy import select
        from datetime import datetime

        try:
            factory = get_session_factory()
            async with factory() as session:
                result = await session.execute(
                    select(Refund).where(
                        Refund.customer_id == item.customer_id,
                        Refund.status == "pending"
                    ).order_by(Refund.created_at.desc())
                )
                refund = result.scalar_one_or_none()
                if refund:
                    refund.status = "approved" if request.decision == "approve" else "rejected"
                    refund.approved_by = "admin"
                    refund.approved_at = datetime.now()
                    if request.comment and request.decision == "reject":
                        refund.rejection_reason = request.comment
                    await session.commit()
                    logger.info("refund_status_updated", refund_no=refund.refund_no, status=refund.status)
        except Exception as e:
            logger.warning("failed_to_update_refund_status", error=str(e))

    await manager.send_event(item.conversation_id, {
        "type": "approval_result",
        "approval_id": approval_id,
        "decision": request.decision,
        "comment": request.comment,
    })

    return {"success": True, "item": item.model_dump()}


@router.post("/conversations/{conversation_id}/takeover")
async def take_over_conversation(conversation_id: str, request: TakeoverRequest) -> dict:
    await manager.send_event(conversation_id, {
        "type": "human_takeover",
        "agent_id": request.agent_id,
        "reason": request.reason,
    })

    logger.info(
        "human_takeover",
        conversation_id=conversation_id,
        agent_id=request.agent_id,
    )

    return {
        "success": True,
        "message": "已接管会话",
        "conversation_id": conversation_id,
    }


@router.post("/conversations/{conversation_id}/release")
async def release_conversation(conversation_id: str) -> dict:
    await manager.send_event(conversation_id, {
        "type": "human_release",
        "message": "人工客服已释放会话，AI将继续处理",
    })

    logger.info("human_release", conversation_id=conversation_id)

    return {
        "success": True,
        "message": "会话已交还AI处理",
        "conversation_id": conversation_id,
    }
