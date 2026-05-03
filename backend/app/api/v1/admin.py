from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.api.websocket.chat_ws import manager
from backend.app.services.approval_queue import get_approval_queue

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
        from datetime import datetime

        from sqlalchemy import select

        from backend.app.core.database import get_session_factory
        from backend.app.models.db.ecommerce import Refund

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

    # 通知Redis等待中的workflow（如果有）
    from backend.app.services.hitl_blocker import get_hitl_blocker
    hitl_blocker = get_hitl_blocker()
    hitl_blocker.notify(approval_id, request.decision)

    await manager.send_event(item.conversation_id, {
        "type": "approval_result",
        "approval_id": approval_id,
        "decision": request.decision,
        "comment": request.comment,
    })

    # 广播到所有在线的管理员
    from backend.app.api.websocket.admin_ws import admin_manager
    await admin_manager.broadcast_approval_update(
        approval_id,
        request.decision,
        item.model_dump(),
    )

    # 发送 webhook 通知
    from backend.app.services.webhook import get_webhook_service
    webhook = get_webhook_service()
    event_type = "approval.approved" if request.decision == "approve" else "approval.rejected"
    await webhook.notify(event_type, {
        "approval_id": approval_id,
        "conversation_id": item.conversation_id,
        "customer_id": item.customer_id,
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


class WebhookRegisterRequest(BaseModel):
    url: str


class WebhookRegisterResponse(BaseModel):
    success: bool
    message: str


@router.post("/webhooks")
async def register_webhook(request: WebhookRegisterRequest) -> WebhookRegisterResponse:
    from backend.app.services.webhook import get_webhook_service

    webhook = get_webhook_service()
    if webhook.register(request.url):
        return WebhookRegisterResponse(success=True, message="Webhook registered")
    return WebhookRegisterResponse(success=False, message="Invalid URL")


@router.delete("/webhooks/{url}")
async def unregister_webhook(url: str) -> dict:
    from backend.app.services.webhook import get_webhook_service

    webhook = get_webhook_service()
    webhook.unregister(url)
    return {"success": True}
