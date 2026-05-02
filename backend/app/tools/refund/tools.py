from __future__ import annotations

import json
import uuid
from datetime import datetime

from langchain_core.tools import tool
from sqlalchemy import select

from backend.app.core.database import get_session_factory
from backend.app.models.db.ecommerce import Order, OrderItem, Refund
from backend.app.services.workflows.refund import get_refund_workflow


@tool
async def order_lookup(customer_id: str, status: str | None = None) -> str:
    """查询客户的订单列表。

    Args:
        customer_id: 客户ID
        status: 可选的状态过滤 (pending/processing/shipped/delivered/cancelled)
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            query = select(Order).where(Order.customer_id == customer_id)
            if status:
                query = query.where(Order.status == status)
            query = query.order_by(Order.created_at.desc())

            result = await session.execute(query)
            orders = result.scalars().all()

            if not orders:
                return f"客户 {customer_id} 暂无订单记录"

            data = []
            for o in orders:
                # 查询订单商品
                items_result = await session.execute(
                    select(OrderItem).where(OrderItem.order_id == o.id)
                )
                items = items_result.scalars().all()

                data.append({
                    "order_no": o.order_no,
                    "status": o.status,
                    "total_amount": float(o.total_amount),
                    "created_at": o.created_at.isoformat(),
                    "items": [
                        {"name": i.product_name, "quantity": i.quantity, "price": float(i.unit_price)}
                        for i in items
                    ],
                })

            return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"查询失败: {str(e)}"}, ensure_ascii=False)


@tool
async def refund_eligibility(order_no: str) -> str:
    """检查订单是否符合退款条件。

    Args:
        order_no: 订单号
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            # 查询订单
            result = await session.execute(
                select(Order).where(Order.order_no == order_no)
            )
            order = result.scalar_one_or_none()

            if not order:
                return json.dumps({"error": f"未找到订单: {order_no}"}, ensure_ascii=False)

            # 查询是否已有退款
            refund_result = await session.execute(
                select(Refund).where(Refund.order_id == order.id)
            )
            existing_refund = refund_result.scalar_one_or_none()

            # 判断退款资格
            eligible = True
            reason = ""

            if order.status == "cancelled":
                eligible = False
                reason = "订单已取消"
            elif existing_refund:
                eligible = False
                reason = f"已有退款申请: {existing_refund.refund_no}"
            elif order.status not in ["delivered", "shipped"]:
                eligible = False
                reason = f"订单状态({order.status})不允许退款"

            # 获取审批级别
            workflow = get_refund_workflow()
            approval_level = workflow.determine_approval_level(float(order.total_amount))

            return json.dumps({
                "order_no": order_no,
                "eligible": eligible,
                "reason": reason,
                "order_status": order.status,
                "order_amount": float(order.total_amount),
                "approval_level": approval_level.value,
                "approval_description": workflow.get_approval_description(
                    type('obj', (object,), {'required_approval': approval_level})()
                ),
            }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"查询失败: {str(e)}"}, ensure_ascii=False)


@tool
async def process_refund(order_no: str, amount: float, reason: str) -> str:
    """处理退款申请。根据金额自动确定审批级别：
    - ≤500元：客服可直接处理
    - 500-2000元：需要主管审批
    - >2000元：需要财务审批

    Args:
        order_no: 订单号
        amount: 退款金额
        reason: 退款原因
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            # 查询订单
            result = await session.execute(
                select(Order).where(Order.order_no == order_no)
            )
            order = result.scalar_one_or_none()

            if not order:
                return json.dumps({"error": f"未找到订单: {order_no}"}, ensure_ascii=False)

            if amount > float(order.total_amount):
                return json.dumps({
                    "error": f"退款金额({amount})超过订单金额({float(order.total_amount)})"
                }, ensure_ascii=False)

            # 使用退款工作流
            workflow = get_refund_workflow()
            refund_request = workflow.create_request(
                order_no=order_no,
                customer_id=order.customer_id,
                amount=amount,
                reason=reason,
            )

            # 根据审批级别处理
            if refund_request.required_approval.value == "agent":
                # 客服可直接批准
                workflow.approve(refund_request, approver="system_agent", comment="客服直接批准")
                initial_status = "approved"
                message = f"退款申请已批准（客服直接处理），金额: ¥{amount}，预计3-5个工作日到账"
            else:
                # 需要主管或财务审批
                initial_status = "pending"
                if refund_request.required_approval.value == "supervisor":
                    message = f"退款申请已提交，需要主管审批（金额: ¥{amount}），预计1-2个工作日完成审批"
                else:
                    message = f"退款申请已提交，需要财务审批（金额: ¥{amount}），预计3-5个工作日完成审批"

            # 创建退款记录
            refund_no = refund_request.id
            refund = Refund(
                refund_no=refund_no,
                order_id=order.id,
                customer_id=order.customer_id,
                amount=amount,
                reason=reason,
                status=initial_status,
            )
            session.add(refund)
            await session.commit()

            return json.dumps({
                "refund_no": refund_no,
                "order_no": order_no,
                "amount": amount,
                "reason": reason,
                "status": initial_status,
                "approval_level": refund_request.required_approval.value,
                "approval_chain": refund_request.approval_chain,
                "message": message,
            }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"退款处理失败: {str(e)}"}, ensure_ascii=False)


@tool
async def refund_status_lookup(order_no: str) -> str:
    """查询退款进度状态。

    Args:
        order_no: 订单号
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            result = await session.execute(
                select(Order).where(Order.order_no == order_no)
            )
            order = result.scalar_one_or_none()

            if not order:
                return json.dumps({"error": f"未找到订单: {order_no}"}, ensure_ascii=False)

            refund_result = await session.execute(
                select(Refund).where(Refund.order_id == order.id)
            )
            refund = refund_result.scalar_one_or_none()

            if not refund:
                return json.dumps({
                    "order_no": order_no,
                    "has_refund": False,
                    "message": "该订单暂无退款申请",
                }, ensure_ascii=False)

            return json.dumps({
                "order_no": order_no,
                "has_refund": True,
                "refund_no": refund.refund_no,
                "amount": float(refund.amount),
                "reason": refund.reason,
                "status": refund.status,
                "created_at": refund.created_at.isoformat(),
                "message": _get_refund_status_message(refund.status),
            }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"查询退款状态失败: {str(e)}"}, ensure_ascii=False)


def _get_refund_status_message(status: str) -> str:
    messages = {
        "pending": "退款申请已提交，等待审批中",
        "approved": "退款已批准处理中",
        "rejected": "退款申请被拒绝",
        "processing": "退款正在处理中，预计3-5个工作日到账",
        "completed": "退款已完成",
        "cancelled": "退款申请已取消",
    }
    return messages.get(status, f"未知状态: {status}")
