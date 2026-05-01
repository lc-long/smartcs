from __future__ import annotations

from langchain_core.tools import tool


@tool
async def knowledge_search(query: str, category: str | None = None, top_k: int = 3) -> str:
    """从知识库中搜索与查询相关的文档片段。

    Args:
        query: 搜索查询
        category: 可选的文档类别过滤
        top_k: 返回结果数量，默认3
    """
    mock_results = [
        {
            "content": "如果您遇到设备无法开机，请先检查电源连接是否正常，然后长按电源键10秒进行强制重启。",
            "source": "故障排查手册",
            "relevance": 0.95,
        },
        {
            "content": "设备连接WiFi失败时，请确认WiFi密码正确，路由器工作正常，设备距离路由器不超过10米。",
            "source": "网络设置指南",
            "relevance": 0.87,
        },
        {
            "content": "系统更新后如出现异常，请尝试清除缓存并重启设备。如问题持续，请联系技术支持。",
            "source": "常见问题FAQ",
            "relevance": 0.82,
        },
    ]

    import json
    return json.dumps(mock_results[:top_k], ensure_ascii=False)


@tool
async def ticket_create(customer_id: str, title: str, description: str, priority: str = "medium") -> str:
    """创建技术支持工单。

    Args:
        customer_id: 客户ID
        title: 工单标题
        description: 问题描述
        priority: 优先级 (low/medium/high/critical)
    """
    import uuid
    ticket = {
        "ticket_id": f"TK-{uuid.uuid4().hex[:8].upper()}",
        "customer_id": customer_id,
        "title": title,
        "description": description,
        "priority": priority,
        "status": "open",
    }
    import json
    return json.dumps(ticket, ensure_ascii=False)


@tool
async def ticket_lookup(customer_id: str, status: str | None = None) -> str:
    """查询客户的技术工单列表。

    Args:
        customer_id: 客户ID
        status: 可选的状态过滤 (open/in_progress/resolved/closed)
    """
    mock_tickets = {
        "C001": [
            {"ticket_id": "TK-A1B2C3D4", "title": "设备无法开机", "status": "resolved", "created": "2024-12-20"},
            {"ticket_id": "TK-E5F6G7H8", "title": "WiFi连接不稳定", "status": "open", "created": "2025-01-10"},
        ],
    }

    tickets = mock_tickets.get(customer_id, [])
    if status:
        tickets = [t for t in tickets if t["status"] == status]

    if not tickets:
        return f"客户 {customer_id} 暂无工单记录"

    import json
    return json.dumps(tickets, ensure_ascii=False)


@tool
async def product_info(product_name: str | None = None) -> str:
    """查询产品信息，包括功能说明、规格参数等。

    Args:
        product_name: 产品名称，不传则返回产品列表
    """
    products = {
        "智能手表Pro": {
            "description": "高端智能手表，支持心率监测、GPS定位、NFC支付",
            "price": 1999.00,
            "warranty": "2年",
        },
        "智能手环Lite": {
            "description": "轻量级运动手环，支持步数统计、睡眠监测",
            "price": 299.00,
            "warranty": "1年",
        },
    }

    if product_name:
        info = products.get(product_name)
        if info:
            import json
            return json.dumps({product_name: info}, ensure_ascii=False)
        return f"未找到产品: {product_name}"

    import json
    return json.dumps(list(products.keys()), ensure_ascii=False)
