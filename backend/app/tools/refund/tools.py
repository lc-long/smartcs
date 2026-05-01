from __future__ import annotations

from langchain_core.tools import tool


@tool
async def order_lookup(order_id: str | None = None, customer_id: str | None = None) -> str:
    """查询订单信息。

    Args:
        order_id: 订单ID，与customer_id二选一
        customer_id: 客户ID，查询该客户所有订单
    """
    mock_orders = {
        "ORD001": {
            "order_id": "ORD001",
            "customer_id": "C001",
            "product": "智能手表Pro",
            "amount": 1999.00,
            "status": "delivered",
            "purchase_date": "2024-12-15",
            "delivery_date": "2024-12-18",
        },
        "ORD002": {
            "order_id": "ORD002",
            "customer_id": "C002",
            "product": "智能手环Lite",
            "amount": 299.00,
            "status": "delivered",
            "purchase_date": "2025-01-02",
            "delivery_date": "2025-01-04",
        },
    }

    if order_id:
        order = mock_orders.get(order_id)
        if order:
            import json
            return json.dumps(order, ensure_ascii=False)
        return f"未找到订单: {order_id}"

    if customer_id:
        orders = [o for o in mock_orders.values() if o["customer_id"] == customer_id]
        import json
        return json.dumps(orders, ensure_ascii=False) if orders else "该客户暂无订单"

    return "请提供订单ID或客户ID"


@tool
async def refund_eligibility(order_id: str) -> str:
    """检查订单是否符合退款条件。

    Args:
        order_id: 订单ID
    """
    mock_eligibility = {
        "ORD001": {
            "eligible": True,
            "reason": "商品在30天退款期内",
            "refund_deadline": "2025-01-14",
            "refund_amount": 1999.00,
        },
        "ORD002": {
            "eligible": False,
            "reason": "商品已超过30天退款期",
            "refund_deadline": "2025-02-01",
            "refund_amount": 0.00,
        },
    }

    result = mock_eligibility.get(order_id)
    if result:
        import json
        return json.dumps(result, ensure_ascii=False)
    return f"未找到订单 {order_id} 的退款信息"


@tool
async def process_refund(order_id: str, reason: str, amount: float | None = None) -> str:
    """处理退款请求。此操作需要人工审批。

    Args:
        order_id: 订单ID
        reason: 退款原因
        amount: 退款金额，不传则全额退款
    """
    import uuid

    refund_request = {
        "refund_id": f"RF-{uuid.uuid4().hex[:8].upper()}",
        "order_id": order_id,
        "reason": reason,
        "amount": amount,
        "status": "pending_approval",
        "message": "退款申请已提交，正在等待人工审批",
    }
    import json
    return json.dumps(refund_request, ensure_ascii=False)
