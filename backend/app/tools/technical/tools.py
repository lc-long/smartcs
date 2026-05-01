from __future__ import annotations

import json
import uuid
from datetime import datetime

from langchain_core.tools import tool
from sqlalchemy import select

from backend.app.core.database import get_session_factory
from backend.app.models.db.ecommerce import KnowledgeArticle, Product, SupportTicket


@tool
async def knowledge_search(query: str, category: str | None = None, top_k: int = 3) -> str:
    """从知识库中搜索与查询相关的文档。

    Args:
        query: 搜索查询
        category: 可选的文档类别过滤
        top_k: 返回结果数量，默认3
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            # 简单的关键词搜索（生产环境应使用向量搜索）
            search_query = select(KnowledgeArticle).where(
                KnowledgeArticle.is_published == True
            )
            if category:
                search_query = search_query.where(KnowledgeArticle.category == category)

            result = await session.execute(search_query)
            articles = result.scalars().all()

            # 简单的关键词匹配评分
            scored = []
            for article in articles:
                score = 0
                query_lower = query.lower()
                if query_lower in article.title.lower():
                    score += 3
                if query_lower in article.content.lower():
                    score += 2
                if article.tags and query_lower in article.tags.lower():
                    score += 1
                if score > 0:
                    scored.append((score, article))

            scored.sort(key=lambda x: x[0], reverse=True)

            if not scored:
                return json.dumps(
                    [{"content": "未找到相关知识文档", "source": "知识库", "relevance": 0}],
                    ensure_ascii=False,
                )

            results = []
            for score, article in scored[:top_k]:
                results.append({
                    "content": article.content[:500],
                    "source": article.title,
                    "relevance": min(score / 5, 1.0),
                    "category": article.category,
                })

            return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"搜索失败: {str(e)}"}, ensure_ascii=False)


@tool
async def ticket_create(customer_id: str, title: str, description: str, priority: str = "medium") -> str:
    """创建技术支持工单。

    Args:
        customer_id: 客户ID
        title: 工单标题
        description: 问题描述
        priority: 优先级 (low/medium/high/critical)
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            ticket_no = f"TK-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
            ticket = SupportTicket(
                ticket_no=ticket_no,
                customer_id=customer_id,
                category="technical",
                title=title,
                description=description,
                priority=priority,
                status="open",
            )
            session.add(ticket)
            await session.commit()

            return json.dumps({
                "ticket_no": ticket_no,
                "customer_id": customer_id,
                "title": title,
                "priority": priority,
                "status": "open",
                "message": "工单创建成功，我们会尽快处理",
            }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"创建工单失败: {str(e)}"}, ensure_ascii=False)


@tool
async def ticket_lookup(customer_id: str, status: str | None = None) -> str:
    """查询客户的工单列表。

    Args:
        customer_id: 客户ID
        status: 可选的状态过滤 (open/in_progress/resolved/closed)
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            query = select(SupportTicket).where(SupportTicket.customer_id == customer_id)
            if status:
                query = query.where(SupportTicket.status == status)
            query = query.order_by(SupportTicket.created_at.desc())

            result = await session.execute(query)
            tickets = result.scalars().all()

            if not tickets:
                return f"客户 {customer_id} 暂无工单记录"

            data = []
            for t in tickets:
                data.append({
                    "ticket_no": t.ticket_no,
                    "title": t.title,
                    "category": t.category,
                    "priority": t.priority,
                    "status": t.status,
                    "created_at": t.created_at.isoformat(),
                })

            return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"查询失败: {str(e)}"}, ensure_ascii=False)


@tool
async def product_info(product_name: str | None = None) -> str:
    """查询产品信息，包括功能说明、规格参数等。

    Args:
        product_name: 产品名称，不传则返回产品列表
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            if product_name:
                query = select(Product).where(
                    Product.name.contains(product_name),
                    Product.is_active == True,
                )
                result = await session.execute(query)
                products = result.scalars().all()
            else:
                query = select(Product).where(Product.is_active == True)
                result = await session.execute(query)
                products = result.scalars().all()

            if not products:
                return f"未找到产品: {product_name}" if product_name else "暂无产品信息"

            data = []
            for p in products:
                data.append({
                    "sku": p.sku,
                    "name": p.name,
                    "description": p.description,
                    "category": p.category,
                    "price": float(p.price),
                    "stock": p.stock,
                    "warranty_months": p.warranty_months,
                })

            return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"查询失败: {str(e)}"}, ensure_ascii=False)
