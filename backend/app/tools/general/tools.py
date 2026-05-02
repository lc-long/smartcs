from __future__ import annotations

import json

from langchain_core.tools import tool
from sqlalchemy import select

from backend.app.core.database import get_session_factory
from backend.app.models.db.ecommerce import Customer, KnowledgeArticle


@tool
async def faq_search(query: str, top_k: int = 3) -> str:
    """搜索常见问题解答。

    Args:
        query: 搜索问题
        top_k: 返回结果数量，默认3
    """
    try:
        from backend.app.services.knowledge.chroma import get_knowledge_base

        kb = get_knowledge_base()

        results = kb.search(query=query, n_results=top_k, where={"category": "general"})

        if not results:
            return json.dumps(
                [{"question": "未找到相关FAQ", "answer": "请尝试其他关键词或联系人工客服"}],
                ensure_ascii=False,
            )

        output = []
        for r in results:
            output.append({
                "question": r["metadata"].get("title", "FAQ"),
                "answer": r["content"],
                "category": r["metadata"].get("category", "general"),
                "relevance": r.get("score", 0),
            })

        return json.dumps(output, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"搜索失败: {str(e)}"}, ensure_ascii=False)


@tool
async def company_info(info_type: str = "general") -> str:
    """查询公司信息。

    Args:
        info_type: 信息类型 (general/contact/warranty/return_policy)
    """
    info = {
        "general": {
            "name": "智能科技商城",
            "description": "专注于智能穿戴设备和配件的电商平台",
            "founded": "2020年",
            "headquarters": "深圳市南山区",
        },
        "contact": {
            "phone": "400-888-9999",
            "email": "service@smarttech.com",
            "address": "深圳市南山区科技园路1号智能大厦",
            "working_hours": "周一至周日 9:00-21:00",
        },
        "warranty": {
            "手表类": "24个月保修",
            "耳机类": "12个月保修",
            "配件类": "6个月保修",
            "说明": "保修范围包括非人为损坏的质量问题",
        },
        "return_policy": {
            "未拆封": "7天内无理由退款",
            "已拆封": "15天内因质量问题可退款",
            "审核时间": "1-3个工作日",
            "到账时间": "审核通过后3-5个工作日",
        },
    }

    data = info.get(info_type, info["general"])
    return json.dumps(data, ensure_ascii=False)


@tool
async def customer_info(customer_id: str) -> str:
    """查询客户基本信息。

    Args:
        customer_id: 客户ID
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            result = await session.execute(
                select(Customer).where(Customer.id == customer_id)
            )
            customer = result.scalar_one_or_none()

            if not customer:
                return json.dumps({"error": f"未找到客户: {customer_id}"}, ensure_ascii=False)

            return json.dumps({
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
                "address": customer.address,
                "vip_level": customer.vip_level,
                "created_at": customer.created_at.isoformat(),
            }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"查询失败: {str(e)}"}, ensure_ascii=False)
