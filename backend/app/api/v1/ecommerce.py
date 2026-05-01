from __future__ import annotations

from decimal import Decimal
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db_session
from backend.app.models.db.ecommerce import (
    Customer,
    Invoice,
    Order,
    OrderItem,
    Payment,
    Product,
    Refund,
    SupportTicket,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/admin/ecommerce", tags=["ecommerce"])


# ==================== Schemas ====================

class ProductCreate(BaseModel):
    sku: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: str = Field(..., min_length=1, max_length=50)
    price: float = Field(..., gt=0)
    stock: int = Field(0, ge=0)
    warranty_months: int = Field(12, ge=0)
    image_url: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    warranty_months: Optional[int] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None


class OrderUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


# ==================== Dashboard ====================

@router.get("/dashboard/stats")
async def get_dashboard_stats(session: AsyncSession = Depends(get_db_session)):
    """获取仪表盘统计数据"""
    try:
        # 商品统计
        products_result = await session.execute(select(func.count(Product.id)))
        total_products = products_result.scalar() or 0

        # 客户统计
        customers_result = await session.execute(select(func.count(Customer.id)))
        total_customers = customers_result.scalar() or 0

        # 订单统计
        orders_result = await session.execute(select(func.count(Order.id)))
        total_orders = orders_result.scalar() or 0

        # 订单金额统计
        revenue_result = await session.execute(
            select(func.sum(Order.total_amount)).where(Order.status != "cancelled")
        )
        total_revenue = float(revenue_result.scalar() or 0)

        # 待处理订单
        pending_result = await session.execute(
            select(func.count(Order.id)).where(Order.status == "pending")
        )
        pending_orders = pending_result.scalar() or 0

        # 待处理退款
        refunds_result = await session.execute(
            select(func.count(Refund.id)).where(Refund.status == "pending")
        )
        pending_refunds = refunds_result.scalar() or 0

        # 待处理工单
        tickets_result = await session.execute(
            select(func.count(SupportTicket.id)).where(SupportTicket.status == "open")
        )
        open_tickets = tickets_result.scalar() or 0

        # 最近订单
        recent_orders_result = await session.execute(
            select(Order).order_by(Order.created_at.desc()).limit(5)
        )
        recent_orders = []
        for order in recent_orders_result.scalars():
            recent_orders.append({
                "order_no": order.order_no,
                "customer_id": order.customer_id,
                "amount": float(order.total_amount),
                "status": order.status,
                "created_at": order.created_at.isoformat(),
            })

        # 热门商品（按订单数量）
        hot_products_result = await session.execute(
            select(
                OrderItem.product_name,
                func.count(OrderItem.id).label("count"),
                func.sum(OrderItem.subtotal).label("total"),
            )
            .group_by(OrderItem.product_name)
            .order_by(func.count(OrderItem.id).desc())
            .limit(5)
        )
        hot_products = []
        for row in hot_products_result:
            hot_products.append({
                "name": row.product_name,
                "count": row.count,
                "total": float(row.total),
            })

        return {
            "summary": {
                "total_products": total_products,
                "total_customers": total_customers,
                "total_orders": total_orders,
                "total_revenue": total_revenue,
                "pending_orders": pending_orders,
                "pending_refunds": pending_refunds,
                "open_tickets": open_tickets,
            },
            "recent_orders": recent_orders,
            "hot_products": hot_products,
        }
    except Exception as e:
        logger.exception("dashboard_stats_error")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Products ====================

@router.get("/products")
async def list_products(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
):
    """获取商品列表"""
    query = select(Product)
    if category:
        query = query.where(Product.category == category)
    if is_active is not None:
        query = query.where(Product.is_active == is_active)
    query = query.order_by(Product.created_at.desc())

    # 计算总数
    count_result = await session.execute(select(func.count(Product.id)))
    total = count_result.scalar() or 0

    # 分页
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)

    products = []
    for p in result.scalars():
        products.append({
            "id": p.id,
            "sku": p.sku,
            "name": p.name,
            "description": p.description,
            "category": p.category,
            "price": float(p.price),
            "stock": p.stock,
            "warranty_months": p.warranty_months,
            "is_active": p.is_active,
            "image_url": p.image_url,
            "created_at": p.created_at.isoformat(),
        })

    return {
        "items": products,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/products", status_code=201)
async def create_product(
    data: ProductCreate,
    session: AsyncSession = Depends(get_db_session),
):
    """创建商品"""
    product = Product(
        sku=data.sku,
        name=data.name,
        description=data.description,
        category=data.category,
        price=Decimal(str(data.price)),
        stock=data.stock,
        warranty_months=data.warranty_months,
        image_url=data.image_url,
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)

    return {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
    }


@router.get("/products/{product_id}")
async def get_product(
    product_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """获取商品详情"""
    result = await session.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    return {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "description": product.description,
        "category": product.category,
        "price": float(product.price),
        "stock": product.stock,
        "warranty_months": product.warranty_months,
        "is_active": product.is_active,
        "image_url": product.image_url,
        "created_at": product.created_at.isoformat(),
        "updated_at": product.updated_at.isoformat(),
    }


@router.put("/products/{product_id}")
async def update_product(
    product_id: str,
    data: ProductUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    """更新商品"""
    result = await session.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    if data.name is not None:
        product.name = data.name
    if data.description is not None:
        product.description = data.description
    if data.category is not None:
        product.category = data.category
    if data.price is not None:
        product.price = Decimal(str(data.price))
    if data.stock is not None:
        product.stock = data.stock
    if data.warranty_months is not None:
        product.warranty_months = data.warranty_months
    if data.image_url is not None:
        product.image_url = data.image_url
    if data.is_active is not None:
        product.is_active = data.is_active

    await session.commit()
    return {"message": "更新成功"}


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """删除商品（软删除）"""
    result = await session.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    product.is_active = False
    await session.commit()
    return {"message": "删除成功"}


# ==================== Orders ====================

@router.get("/orders")
async def list_orders(
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
):
    """获取订单列表"""
    query = select(Order)
    if status:
        query = query.where(Order.status == status)
    if customer_id:
        query = query.where(Order.customer_id == customer_id)
    query = query.order_by(Order.created_at.desc())

    # 计算总数
    count_result = await session.execute(select(func.count(Order.id)))
    total = count_result.scalar() or 0

    # 分页
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)

    orders = []
    for o in result.scalars():
        # 查询订单商品
        items_result = await session.execute(
            select(OrderItem).where(OrderItem.order_id == o.id)
        )
        items = []
        for item in items_result.scalars():
            items.append({
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
                "subtotal": float(item.subtotal),
            })

        orders.append({
            "id": o.id,
            "order_no": o.order_no,
            "customer_id": o.customer_id,
            "status": o.status,
            "total_amount": float(o.total_amount),
            "shipping_address": o.shipping_address,
            "notes": o.notes,
            "items": items,
            "created_at": o.created_at.isoformat(),
        })

    return {
        "items": orders,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/orders/{order_id}")
async def get_order(
    order_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """获取订单详情"""
    result = await session.execute(
        select(Order).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 查询订单商品
    items_result = await session.execute(
        select(OrderItem).where(OrderItem.order_id == order.id)
    )
    items = []
    for item in items_result.scalars():
        items.append({
            "product_name": item.product_name,
            "quantity": item.quantity,
            "unit_price": float(item.unit_price),
            "subtotal": float(item.subtotal),
        })

    # 查询支付记录
    payments_result = await session.execute(
        select(Payment).where(Payment.order_id == order.id)
    )
    payments = []
    for p in payments_result.scalars():
        payments.append({
            "payment_no": p.payment_no,
            "amount": float(p.amount),
            "method": p.method,
            "status": p.status,
            "created_at": p.created_at.isoformat(),
        })

    # 查询退款记录
    refunds_result = await session.execute(
        select(Refund).where(Refund.order_id == order.id)
    )
    refunds = []
    for r in refunds_result.scalars():
        refunds.append({
            "refund_no": r.refund_no,
            "amount": float(r.amount),
            "reason": r.reason,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
        })

    return {
        "id": order.id,
        "order_no": order.order_no,
        "customer_id": order.customer_id,
        "status": order.status,
        "total_amount": float(order.total_amount),
        "shipping_address": order.shipping_address,
        "notes": order.notes,
        "items": items,
        "payments": payments,
        "refunds": refunds,
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
    }


@router.put("/orders/{order_id}")
async def update_order(
    order_id: str,
    data: OrderUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    """更新订单状态"""
    result = await session.execute(
        select(Order).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if data.status is not None:
        order.status = data.status
    if data.notes is not None:
        order.notes = data.notes

    await session.commit()
    return {"message": "更新成功"}


# ==================== Customers ====================

@router.get("/customers")
async def list_customers(
    vip_level: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
):
    """获取客户列表"""
    query = select(Customer)
    if vip_level:
        query = query.where(Customer.vip_level == vip_level)
    query = query.order_by(Customer.created_at.desc())

    # 计算总数
    count_result = await session.execute(select(func.count(Customer.id)))
    total = count_result.scalar() or 0

    # 分页
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)

    customers = []
    for c in result.scalars():
        # 查询客户订单数
        orders_count_result = await session.execute(
            select(func.count(Order.id)).where(Order.customer_id == c.id)
        )
        orders_count = orders_count_result.scalar() or 0

        # 查询客户消费总额
        total_spent_result = await session.execute(
            select(func.sum(Order.total_amount))
            .where(Order.customer_id == c.id)
            .where(Order.status != "cancelled")
        )
        total_spent = float(total_spent_result.scalar() or 0)

        customers.append({
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "address": c.address,
            "vip_level": c.vip_level,
            "orders_count": orders_count,
            "total_spent": total_spent,
            "created_at": c.created_at.isoformat(),
        })

    return {
        "items": customers,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/customers/{customer_id}")
async def get_customer(
    customer_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """获取客户详情"""
    result = await session.execute(
        select(Customer).where(Customer.id == customer_id)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    # 查询最近订单
    orders_result = await session.execute(
        select(Order)
        .where(Order.customer_id == customer_id)
        .order_by(Order.created_at.desc())
        .limit(10)
    )
    orders = []
    for o in orders_result.scalars():
        orders.append({
            "order_no": o.order_no,
            "amount": float(o.total_amount),
            "status": o.status,
            "created_at": o.created_at.isoformat(),
        })

    # 查询最近工单
    tickets_result = await session.execute(
        select(SupportTicket)
        .where(SupportTicket.customer_id == customer_id)
        .order_by(SupportTicket.created_at.desc())
        .limit(5)
    )
    tickets = []
    for t in tickets_result.scalars():
        tickets.append({
            "ticket_no": t.ticket_no,
            "title": t.title,
            "status": t.status,
            "created_at": t.created_at.isoformat(),
        })

    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "address": customer.address,
        "vip_level": customer.vip_level,
        "orders": orders,
        "tickets": tickets,
        "created_at": customer.created_at.isoformat(),
    }


# ==================== Refunds ====================

@router.get("/refunds")
async def list_refunds(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
):
    """获取退款列表"""
    query = select(Refund)
    if status:
        query = query.where(Refund.status == status)
    query = query.order_by(Refund.created_at.desc())

    # 计算总数
    count_result = await session.execute(select(func.count(Refund.id)))
    total = count_result.scalar() or 0

    # 分页
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)

    refunds = []
    for r in result.scalars():
        refunds.append({
            "id": r.id,
            "refund_no": r.refund_no,
            "order_id": r.order_id,
            "customer_id": r.customer_id,
            "amount": float(r.amount),
            "reason": r.reason,
            "status": r.status,
            "approved_by": r.approved_by,
            "created_at": r.created_at.isoformat(),
        })

    return {
        "items": refunds,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.put("/refunds/{refund_id}/approve")
async def approve_refund(
    refund_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """审批退款"""
    from datetime import datetime

    result = await session.execute(
        select(Refund).where(Refund.id == refund_id)
    )
    refund = result.scalar_one_or_none()
    if not refund:
        raise HTTPException(status_code=404, detail="退款记录不存在")

    if refund.status != "pending":
        raise HTTPException(status_code=400, detail="退款已处理")

    refund.status = "approved"
    refund.approved_by = "admin"
    refund.approved_at = datetime.now()
    await session.commit()

    return {"message": "退款已批准"}


@router.put("/refunds/{refund_id}/reject")
async def reject_refund(
    refund_id: str,
    reason: str = "",
    session: AsyncSession = Depends(get_db_session),
):
    """拒绝退款"""
    from datetime import datetime

    result = await session.execute(
        select(Refund).where(Refund.id == refund_id)
    )
    refund = result.scalar_one_or_none()
    if not refund:
        raise HTTPException(status_code=404, detail="退款记录不存在")

    if refund.status != "pending":
        raise HTTPException(status_code=400, detail="退款已处理")

    refund.status = "rejected"
    refund.approved_by = "admin"
    refund.approved_at = datetime.now()
    await session.commit()

    return {"message": "退款已拒绝"}


# ==================== Knowledge Base ====================

@router.get("/knowledge")
async def list_knowledge(
    category: Optional[str] = None,
    session: AsyncSession = Depends(get_db_session),
):
    """获取知识库文章列表"""
    from backend.app.models.db.ecommerce import KnowledgeArticle

    query = select(KnowledgeArticle)
    if category:
        query = query.where(KnowledgeArticle.category == category)
    query = query.order_by(KnowledgeArticle.created_at.desc())

    result = await session.execute(query)
    articles = []
    for a in result.scalars():
        articles.append({
            "id": a.id,
            "title": a.title,
            "category": a.category,
            "view_count": a.view_count,
            "is_published": a.is_published,
            "created_at": a.created_at.isoformat(),
        })

    return {"items": articles}
