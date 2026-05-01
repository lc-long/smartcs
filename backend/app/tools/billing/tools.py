from __future__ import annotations

import json
from datetime import datetime

from langchain_core.tools import tool
from sqlalchemy import select

from backend.app.core.database import get_session_factory
from backend.app.models.db.ecommerce import Invoice, Order, Payment


@tool
async def invoice_lookup(customer_id: str, status: str | None = None) -> str:
    """查询客户的发票/账单列表。

    Args:
        customer_id: 客户ID
        status: 可选的状态过滤 (pending/paid/overdue)
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            query = select(Invoice).where(Invoice.customer_id == customer_id)
            if status:
                query = query.where(Invoice.status == status)
            query = query.order_by(Invoice.created_at.desc())

            result = await session.execute(query)
            invoices = result.scalars().all()

            if not invoices:
                return f"客户 {customer_id} 暂无账单记录"

            data = []
            for inv in invoices:
                data.append({
                    "invoice_no": inv.invoice_no,
                    "amount": float(inv.amount),
                    "status": inv.status,
                    "due_date": inv.due_date.isoformat() if inv.due_date else None,
                    "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
                })

            return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"查询失败: {str(e)}"}, ensure_ascii=False)


@tool
async def payment_history(customer_id: str, limit: int = 10) -> str:
    """查询客户的支付历史记录。

    Args:
        customer_id: 客户ID
        limit: 返回记录数量，默认10
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            query = (
                select(Payment)
                .where(Payment.customer_id == customer_id)
                .order_by(Payment.created_at.desc())
                .limit(limit)
            )

            result = await session.execute(query)
            payments = result.scalars().all()

            if not payments:
                return f"客户 {customer_id} 暂无支付记录"

            data = []
            for pay in payments:
                data.append({
                    "payment_no": pay.payment_no,
                    "order_id": pay.order_id,
                    "amount": float(pay.amount),
                    "method": pay.method,
                    "status": pay.status,
                    "created_at": pay.created_at.isoformat(),
                })

            return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"查询失败: {str(e)}"}, ensure_ascii=False)


@tool
async def billing_summary(customer_id: str) -> str:
    """获取客户的账单汇总信息。

    Args:
        customer_id: 客户ID
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            # 查询所有发票
            result = await session.execute(
                select(Invoice).where(Invoice.customer_id == customer_id)
            )
            invoices = result.scalars().all()

            total_amount = sum(float(inv.amount) for inv in invoices)
            paid_amount = sum(float(inv.amount) for inv in invoices if inv.status == "paid")
            pending_amount = sum(float(inv.amount) for inv in invoices if inv.status == "pending")

            # 查询最近订单
            order_result = await session.execute(
                select(Order)
                .where(Order.customer_id == customer_id)
                .order_by(Order.created_at.desc())
                .limit(5)
            )
            recent_orders = order_result.scalars().all()

            summary = {
                "customer_id": customer_id,
                "total_invoices": len(invoices),
                "total_amount": total_amount,
                "paid_amount": paid_amount,
                "pending_amount": pending_amount,
                "recent_orders": [
                    {
                        "order_no": o.order_no,
                        "amount": float(o.total_amount),
                        "status": o.status,
                    }
                    for o in recent_orders
                ],
            }

            return json.dumps(summary, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"查询失败: {str(e)}"}, ensure_ascii=False)
