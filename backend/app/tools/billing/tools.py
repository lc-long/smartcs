from __future__ import annotations

from langchain_core.tools import tool


@tool
async def invoice_lookup(customer_id: str, month: str | None = None) -> str:
    """查询客户的发票信息。如果指定了月份，返回该月的发票；否则返回最近的发票。

    Args:
        customer_id: 客户ID
        month: 查询月份，格式 YYYY-MM，不传则返回最近发票
    """
    mock_invoices = {
        "C001": [
            {"month": "2025-01", "amount": 299.00, "status": "paid", "items": "基础套餐"},
            {"month": "2024-12", "amount": 299.00, "status": "paid", "items": "基础套餐"},
        ],
        "C002": [
            {"month": "2025-01", "amount": 599.00, "status": "unpaid", "items": "高级套餐"},
        ],
    }

    invoices = mock_invoices.get(customer_id, [])
    if month:
        invoices = [i for i in invoices if i["month"] == month]

    if not invoices:
        return f"未找到客户 {customer_id} 的发票信息"

    import json
    return json.dumps(invoices, ensure_ascii=False)


@tool
async def payment_history(customer_id: str, limit: int = 5) -> str:
    """查询客户的支付历史记录。

    Args:
        customer_id: 客户ID
        limit: 返回记录数量，默认5条
    """
    mock_history = {
        "C001": [
            {"date": "2025-01-05", "amount": 299.00, "method": "支付宝", "status": "成功"},
            {"date": "2024-12-03", "amount": 299.00, "method": "微信支付", "status": "成功"},
        ],
        "C002": [],
    }

    history = mock_history.get(customer_id, [])
    if not history:
        return f"客户 {customer_id} 暂无支付记录"

    import json
    return json.dumps(history[:limit], ensure_ascii=False)


@tool
async def billing_summary(customer_id: str) -> str:
    """生成客户账单摘要，包括当前欠费、已付金额等。

    Args:
        customer_id: 客户ID
    """
    mock_summaries = {
        "C001": {
            "current_balance": 0.00,
            "total_paid": 3588.00,
            "plan": "基础套餐",
            "next_billing_date": "2025-02-01",
        },
        "C002": {
            "current_balance": 599.00,
            "total_paid": 0.00,
            "plan": "高级套餐",
            "next_billing_date": "2025-02-01",
        },
    }

    summary = mock_summaries.get(customer_id)
    if not summary:
        return f"未找到客户 {customer_id} 的账单摘要"

    import json
    return json.dumps(summary, ensure_ascii=False)
