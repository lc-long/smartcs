from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger()


class RefundStatus(str, Enum):
    PENDING = "pending"              # 待处理
    UNDER_REVIEW = "under_review"    # 审核中
    APPROVED = "approved"            # 已批准
    REJECTED = "rejected"            # 已拒绝
    PROCESSING = "processing"        # 处理中（银行处理）
    COMPLETED = "completed"          # 已完成
    FAILED = "failed"                # 失败


class ApprovalLevel(str, Enum):
    AGENT = "agent"           # 客服可直接批准
    SUPERVISOR = "supervisor"  # 需要主管审批
    FINANCE = "finance"        # 需要财务审批


@dataclass
class RefundRequest:
    """退款申请"""
    id: str
    order_no: str
    customer_id: str
    amount: float
    reason: str
    status: RefundStatus = RefundStatus.PENDING
    required_approval: ApprovalLevel = ApprovalLevel.AGENT
    approval_chain: list[dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None


class RefundWorkflow:
    """退款审批工作流"""

    # 审批级别阈值
    AGENT_LIMIT = 500.0       # 客服可直接批准 ≤500
    SUPERVISOR_LIMIT = 2000.0  # 主管可批准 ≤2000
    # >2000 需要财务审批

    def determine_approval_level(self, amount: float) -> ApprovalLevel:
        """根据金额确定审批级别"""
        if amount <= self.AGENT_LIMIT:
            return ApprovalLevel.AGENT
        elif amount <= self.SUPERVISOR_LIMIT:
            return ApprovalLevel.SUPERVISOR
        else:
            return ApprovalLevel.FINANCE

    def create_request(
        self,
        order_no: str,
        customer_id: str,
        amount: float,
        reason: str,
    ) -> RefundRequest:
        """创建退款申请"""
        request_id = f"REF-{datetime.now().strftime('%Y%m%d%H%M%S')}-{order_no[-4:]}"
        approval_level = self.determine_approval_level(amount)

        request = RefundRequest(
            id=request_id,
            order_no=order_no,
            customer_id=customer_id,
            amount=amount,
            reason=reason,
            required_approval=approval_level,
            approval_chain=[{
                "step": "created",
                "by": "system",
                "time": datetime.now().isoformat(),
                "note": f"退款申请已创建，需要{approval_level.value}审批",
            }],
        )

        logger.info(
            "refund_request_created",
            request_id=request_id,
            amount=amount,
            approval_level=approval_level.value,
        )

        return request

    def approve(
        self,
        request: RefundRequest,
        approver: str,
        comment: str = "",
    ) -> RefundRequest:
        """审批通过"""
        request.status = RefundStatus.APPROVED
        request.approval_chain.append({
            "step": "approved",
            "by": approver,
            "time": datetime.now().isoformat(),
            "note": comment,
        })
        request.updated_at = datetime.now()

        logger.info(
            "refund_approved",
            request_id=request.id,
            approver=approver,
        )

        return request

    def reject(
        self,
        request: RefundRequest,
        approver: str,
        reason: str,
    ) -> RefundRequest:
        """审批拒绝"""
        request.status = RefundStatus.REJECTED
        request.approval_chain.append({
            "step": "rejected",
            "by": approver,
            "time": datetime.now().isoformat(),
            "note": reason,
        })
        request.updated_at = datetime.now()

        logger.info(
            "refund_rejected",
            request_id=request.id,
            approver=approver,
            reason=reason,
        )

        return request

    def start_processing(self, request: RefundRequest) -> RefundRequest:
        """开始处理退款（银行处理）"""
        request.status = RefundStatus.PROCESSING
        request.approval_chain.append({
            "step": "processing",
            "by": "system",
            "time": datetime.now().isoformat(),
            "note": "退款已提交给银行处理",
        })
        request.updated_at = datetime.now()

        return request

    def complete(self, request: RefundRequest) -> RefundRequest:
        """退款完成"""
        request.status = RefundStatus.COMPLETED
        request.completed_at = datetime.now()
        request.approval_chain.append({
            "step": "completed",
            "by": "system",
            "time": datetime.now().isoformat(),
            "note": "退款已到账",
        })
        request.updated_at = datetime.now()

        return request

    def get_status_description(self, request: RefundRequest) -> str:
        """获取状态描述"""
        status_desc = {
            RefundStatus.PENDING: "待处理",
            RefundStatus.UNDER_REVIEW: "审核中",
            RefundStatus.APPROVED: "已批准，等待处理",
            RefundStatus.REJECTED: "已拒绝",
            RefundStatus.PROCESSING: "银行处理中",
            RefundStatus.COMPLETED: "已完成",
            RefundStatus.FAILED: "处理失败",
        }
        return status_desc.get(request.status, "未知状态")

    def get_approval_description(self, request: RefundRequest) -> str:
        """获取审批级别描述"""
        if request.required_approval == ApprovalLevel.AGENT:
            return "客服可直接处理"
        elif request.required_approval == ApprovalLevel.SUPERVISOR:
            return "需要主管审批"
        else:
            return "需要财务审批"


_workflow: RefundWorkflow | None = None


def get_refund_workflow() -> RefundWorkflow:
    global _workflow
    if _workflow is None:
        _workflow = RefundWorkflow()
    return _workflow
