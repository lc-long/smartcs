from __future__ import annotations

import json
import uuid
from datetime import datetime
from decimal import Decimal

import structlog
from langchain_core.tools import tool
from sqlalchemy import and_, or_, select

from backend.app.core.database import get_session_factory
from backend.app.models.db.ecommerce import (
    Coupon,
    Customer,
    CustomerCoupon,
    CustomerFeedback,
    Invoice,
    KnowledgeArticle,
    LoyaltyPoints,
    Order,
    OrderItem,
    Payment,
    Product,
    Refund,
    Shipment,
    ShipmentTracking,
    SupportTicket,
)
from backend.app.services.workflows.refund import get_refund_workflow

logger = structlog.get_logger()

# ============================================================================
# ORDER MANAGEMENT TOOLS
# ============================================================================


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
                items_result = await session.execute(
                    select(OrderItem).where(OrderItem.order_id == o.id)
                )
                items = items_result.scalars().all()

                data.append(
                    {
                        "order_no": o.order_no,
                        "status": o.status,
                        "total_amount": float(o.total_amount),
                        "created_at": o.created_at.isoformat(),
                        "items": [
                            {
                                "name": i.product_name,
                                "quantity": i.quantity,
                                "price": float(i.unit_price),
                            }
                            for i in items
                        ],
                    }
                )

            return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"查询失败: {str(e)}"}, ensure_ascii=False)


@tool
async def cancel_order(
    order_no: str,
    customer_id: str,
    reason: str = "客户取消",
) -> str:
    """取消订单。

    Args:
        order_no: 订单号
        customer_id: 客户ID（用于验证）
        reason: 取消原因
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            result = await session.execute(
                select(Order).where(
                    and_(Order.order_no == order_no, Order.customer_id == customer_id)
                )
            )
            order = result.scalar_one_or_none()

            if not order:
                return json.dumps({"success": False, "error": "订单不存在或无权取消"})

            cancellable_statuses = ["pending", "confirmed", "processing"]
            if order.status not in cancellable_statuses:
                return json.dumps(
                    {
                        "success": False,
                        "error": f"当前订单状态为'{order.status}'，无法取消",
                    }
                )

            order.status = "cancelled"
            order.notes = (order.notes or "") + f" [取消原因: {reason}]"

            order_items_result = await session.execute(
                select(OrderItem).where(OrderItem.order_id == order.id)
            )
            for item in order_items_result.scalars():
                product_result = await session.execute(
                    select(Product).where(Product.id == item.product_id)
                )
                product = product_result.scalar_one_or_none()
                if product:
                    product.stock += item.quantity

            await session.commit()

            logger.info("order_cancelled", order_no=order_no, customer_id=customer_id)
            return json.dumps(
                {
                    "success": True,
                    "message": f"订单 {order_no} 已成功取消",
                    "order_no": order_no,
                    "refund_status": "将在3-5个工作日内退款到原支付方式",
                },
                ensure_ascii=False,
            )
    except Exception as e:
        return json.dumps({"success": False, "error": f"取消订单失败: {str(e)}"})


# ============================================================================
# PRODUCT TOOLS
# ============================================================================


@tool
async def create_order(
    customer_id: str,
    product_id: str,
    quantity: int = 1,
    shipping_address: str | None = None,
    notes: str | None = None,
) -> str:
    """创建新订单。

    Args:
        customer_id: 客户ID
        product_id: 产品ID
        quantity: 购买数量，默认1
        shipping_address: 收货地址，如果为空则使用客户默认地址
        notes: 订单备注
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            customer_result = await session.execute(
                select(Customer).where(Customer.id == customer_id)
            )
            customer = customer_result.scalar_one_or_none()
            if not customer:
                return json.dumps({"success": False, "error": f"未找到客户: {customer_id}"})

            product_result = await session.execute(select(Product).where(Product.id == product_id))
            product = product_result.scalar_one_or_none()
            if not product:
                return json.dumps({"success": False, "error": f"未找到产品: {product_id}"})

            if product.stock < quantity:
                return json.dumps(
                    {
                        "success": False,
                        "error": f"库存不足，当前库存: {product.stock}",
                    }
                )

            address = shipping_address or customer.address or "未设置"

            unit_price = Decimal(str(product.price))
            subtotal = unit_price * quantity
            shipping_fee = Decimal("10.00") if subtotal < Decimal("99") else Decimal("0")
            final_amount = subtotal + shipping_fee

            order_no = f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
            order = Order(
                id=str(uuid.uuid4()),
                order_no=order_no,
                customer_id=customer_id,
                status="pending",
                total_amount=subtotal,
                discount_amount=Decimal("0"),
                shipping_fee=shipping_fee,
                final_amount=final_amount,
                shipping_address=address,
                notes=notes,
            )
            session.add(order)

            order_item = OrderItem(
                id=str(uuid.uuid4()),
                order_id=order.id,
                product_id=product_id,
                product_name=product.name,
                quantity=quantity,
                unit_price=unit_price,
                subtotal=subtotal,
            )
            session.add(order_item)

            product.stock -= quantity

            await session.commit()

            logger.info("order_created", order_no=order_no, customer_id=customer_id)
            return json.dumps(
                {
                    "success": True,
                    "order_id": order.id,
                    "order_no": order_no,
                    "product_name": product.name,
                    "quantity": quantity,
                    "unit_price": float(unit_price),
                    "shipping_fee": float(shipping_fee),
                    "final_amount": float(final_amount),
                    "shipping_address": address,
                    "status": "pending",
                },
                ensure_ascii=False,
            )
    except Exception as e:
        return json.dumps({"success": False, "error": f"创建订单失败: {str(e)}"})


@tool
async def search_products(
    query: str,
    max_price: float | None = None,
    limit: int = 10,
) -> str:
    """搜索产品。

    Args:
        query: 搜索关键词（匹配产品名称或描述）
        max_price: 最高价格筛选（可选）
        limit: 返回数量，默认10
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            stmt = select(Product).where(Product.is_active)

            if query:
                search_pattern = f"%{query}%"
                stmt = stmt.where(
                    or_(
                        Product.name.ilike(search_pattern),
                        Product.description.ilike(search_pattern),
                        Product.category.ilike(search_pattern),
                    )
                )

            if max_price is not None:
                stmt = stmt.where(Product.price <= max_price)

            stmt = stmt.order_by(Product.created_at.desc()).limit(limit)

            result = await session.execute(stmt)
            products = result.scalars().all()

            if not products:
                return json.dumps(
                    {
                        "success": True,
                        "products": [],
                        "message": "未找到相关产品",
                    },
                    ensure_ascii=False,
                )

            output = []
            for p in products:
                output.append(
                    {
                        "product_id": p.id,
                        "name": p.name,
                        "price": float(p.price),
                        "stock": p.stock,
                        "category": p.category or "",
                    }
                )

            return json.dumps(
                {
                    "success": True,
                    "products": output,
                    "count": len(output),
                },
                ensure_ascii=False,
            )
    except Exception as e:
        return json.dumps({"success": False, "error": f"搜索失败: {str(e)}"})


@tool
async def get_product_info(product_id: str) -> str:
    """获取产品信息。

    Args:
        product_id: 产品ID
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            result = await session.execute(select(Product).where(Product.id == product_id))
            product = result.scalar_one_or_none()

            if not product:
                return json.dumps({"success": False, "error": f"未找到产品: {product_id}"})

            return json.dumps(
                {
                    "success": True,
                    "product_id": product.id,
                    "name": product.name,
                    "price": float(product.price),
                    "stock": product.stock,
                    "description": product.description or "",
                },
                ensure_ascii=False,
            )
    except Exception as e:
        return json.dumps({"success": False, "error": f"查询失败: {str(e)}"})


@tool
async def get_customer_address(customer_id: str) -> str:
    """获取客户默认收货地址。

    Args:
        customer_id: 客户ID
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            result = await session.execute(select(Customer).where(Customer.id == customer_id))
            customer = result.scalar_one_or_none()

            if not customer:
                return json.dumps({"success": False, "error": f"未找到客户: {customer_id}"})

            return json.dumps(
                {
                    "success": True,
                    "customer_id": customer_id,
                    "name": customer.name,
                    "address": customer.address or "未设置",
                    "phone": customer.phone or "未设置",
                },
                ensure_ascii=False,
            )
    except Exception as e:
        return json.dumps({"success": False, "error": f"查询失败: {str(e)}"})


# ============================================================================
# REFUND TOOLS
# ============================================================================


@tool
async def refund_eligibility(order_no: str) -> str:
    """检查订单是否符合退款条件。

    Args:
        order_no: 订单号
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            result = await session.execute(select(Order).where(Order.order_no == order_no))
            order = result.scalar_one_or_none()

            if not order:
                return json.dumps({"error": f"未找到订单: {order_no}"}, ensure_ascii=False)

            refund_result = await session.execute(select(Refund).where(Refund.order_id == order.id))
            existing_refund = refund_result.scalar_one_or_none()

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

            workflow = get_refund_workflow()
            approval_level = workflow.determine_approval_level(float(order.total_amount))

            return json.dumps(
                {
                    "order_no": order_no,
                    "eligible": eligible,
                    "reason": reason,
                    "order_status": order.status,
                    "order_amount": float(order.total_amount),
                    "approval_level": approval_level.value,
                    "approval_description": workflow.get_approval_description(
                        type("obj", (object,), {"required_approval": approval_level})()
                    ),
                },
                ensure_ascii=False,
            )
    except Exception as e:
        return json.dumps({"error": f"查询失败: {str(e)}"}, ensure_ascii=False)


@tool
async def process_refund(order_no: str, amount: float, reason: str) -> str:
    """处理退款申请。根据金额自动确定审批级别。

    Args:
        order_no: 订单号
        amount: 退款金额
        reason: 退款原因
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            result = await session.execute(select(Order).where(Order.order_no == order_no))
            order = result.scalar_one_or_none()

            if not order:
                return json.dumps({"error": f"未找到订单: {order_no}"}, ensure_ascii=False)

            if amount > float(order.total_amount):
                return json.dumps(
                    {"error": f"退款金额({amount})超过订单金额({float(order.total_amount)})"},
                    ensure_ascii=False,
                )

            workflow = get_refund_workflow()
            refund_request = workflow.create_request(
                order_no=order_no,
                customer_id=order.customer_id,
                amount=amount,
                reason=reason,
            )

            initial_status = "pending"
            if refund_request.required_approval.value == "agent":
                message = f"退款申请已提交（客服直接处理），金额: ¥{amount}，正在等待系统确认"
            elif refund_request.required_approval.value == "supervisor":
                message = (
                    f"退款申请已提交，需要主管审批（金额: ¥{amount}），预计1-2个工作日完成审批"
                )
            else:
                message = (
                    f"退款申请已提交，需要财务审批（金额: ¥{amount}），预计3-5个工作日完成审批"
                )

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

            return json.dumps(
                {
                    "refund_no": refund_no,
                    "order_no": order_no,
                    "amount": amount,
                    "reason": reason,
                    "status": initial_status,
                    "approval_level": refund_request.required_approval.value,
                    "approval_chain": refund_request.approval_chain,
                    "message": message,
                },
                ensure_ascii=False,
            )
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
            result = await session.execute(select(Order).where(Order.order_no == order_no))
            order = result.scalar_one_or_none()

            if not order:
                return json.dumps({"error": f"未找到订单: {order_no}"}, ensure_ascii=False)

            refund_result = await session.execute(select(Refund).where(Refund.order_id == order.id))
            refund = refund_result.scalar_one_or_none()

            if not refund:
                return json.dumps(
                    {
                        "order_no": order_no,
                        "has_refund": False,
                        "message": "该订单暂无退款申请",
                    },
                    ensure_ascii=False,
                )

            return json.dumps(
                {
                    "order_no": order_no,
                    "has_refund": True,
                    "refund_no": refund.refund_no,
                    "amount": float(refund.amount),
                    "reason": refund.reason,
                    "status": refund.status,
                    "created_at": refund.created_at.isoformat(),
                    "message": _get_refund_status_message(refund.status),
                },
                ensure_ascii=False,
            )
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


# ============================================================================
# BILLING TOOLS
# ============================================================================


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
                data.append(
                    {
                        "invoice_no": inv.invoice_no,
                        "amount": float(inv.amount),
                        "status": inv.status,
                        "due_date": inv.due_date.isoformat() if inv.due_date else None,
                        "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
                    }
                )

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
                data.append(
                    {
                        "payment_no": pay.payment_no,
                        "order_id": pay.order_id,
                        "amount": float(pay.amount),
                        "method": pay.method,
                        "status": pay.status,
                        "created_at": pay.created_at.isoformat(),
                    }
                )

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
            result = await session.execute(
                select(Invoice).where(Invoice.customer_id == customer_id)
            )
            invoices = result.scalars().all()

            total_amount = sum(float(inv.amount) for inv in invoices)
            paid_amount = sum(float(inv.amount) for inv in invoices if inv.status == "paid")
            pending_amount = sum(float(inv.amount) for inv in invoices if inv.status == "pending")

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


@tool
async def order_payment_match(order_no: str) -> str:
    """核对订单与支付记录是否匹配，用于账单异常排查。

    Args:
        order_no: 订单号
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            order_result = await session.execute(select(Order).where(Order.order_no == order_no))
            order = order_result.scalar_one_or_none()

            if not order:
                return json.dumps({"error": f"未找到订单: {order_no}"}, ensure_ascii=False)

            items_result = await session.execute(
                select(OrderItem).where(OrderItem.order_id == order.id)
            )
            items = items_result.scalars().all()

            payment_result = await session.execute(
                select(Payment).where(Payment.order_id == order.id)
            )
            payments = payment_result.scalars().all()

            refund_result = await session.execute(select(Refund).where(Refund.order_id == order.id))
            refunds = refund_result.scalars().all()

            total_paid = sum(float(p.amount) for p in payments if p.status == "completed")
            total_refunded = sum(
                float(r.amount) for r in refunds if r.status in ["approved", "completed"]
            )
            order_amount = float(order.total_amount)

            match_result = {
                "order_no": order_no,
                "order_amount": order_amount,
                "total_paid": total_paid,
                "total_refunded": total_refunded,
                "net_amount": total_paid - total_refunded,
                "is_matched": abs(order_amount - total_paid) < 0.01,
                "difference": order_amount - total_paid,
                "items": [
                    {"name": i.product_name, "quantity": i.quantity, "price": float(i.unit_price)}
                    for i in items
                ],
                "payments": [
                    {"payment_no": p.payment_no, "amount": float(p.amount), "status": p.status}
                    for p in payments
                ],
                "refunds": [
                    {"refund_no": r.refund_no, "amount": float(r.amount), "status": r.status}
                    for r in refunds
                ],
            }

            return json.dumps(match_result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"核对失败: {str(e)}"}, ensure_ascii=False)


# ============================================================================
# TECHNICAL SUPPORT TOOLS
# ============================================================================


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
            search_pattern = f"%{query}%"
            stmt = select(KnowledgeArticle).where(
                KnowledgeArticle.is_published,
                or_(
                    KnowledgeArticle.title.ilike(search_pattern),
                    KnowledgeArticle.content.ilike(search_pattern),
                ),
            )
            if category:
                stmt = stmt.where(KnowledgeArticle.category == category)
            stmt = stmt.order_by(KnowledgeArticle.view_count.desc()).limit(top_k)

            result = await session.execute(stmt)
            articles = result.scalars().all()

            if not articles:
                return json.dumps(
                    [{"content": "未找到相关知识文档", "source": "知识库", "relevance": 0}],
                    ensure_ascii=False,
                )

            output = []
            for article in articles:
                title_match = query.lower() in article.title.lower()
                content_match = query.lower() in article.content.lower()
                relevance = 0.9 if title_match else (0.7 if content_match else 0.5)
                output.append(
                    {
                        "content": article.content[:500],
                        "source": article.title,
                        "relevance": relevance,
                        "category": article.category,
                    }
                )

            return json.dumps(output, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"搜索失败: {str(e)}"}, ensure_ascii=False)


@tool
async def ticket_create(
    customer_id: str, title: str, description: str, priority: str = "medium"
) -> str:
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

            return json.dumps(
                {
                    "ticket_no": ticket_no,
                    "customer_id": customer_id,
                    "title": title,
                    "priority": priority,
                    "status": "open",
                    "message": "工单创建成功，我们会尽快处理",
                },
                ensure_ascii=False,
            )
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
                data.append(
                    {
                        "ticket_no": t.ticket_no,
                        "title": t.title,
                        "category": t.category,
                        "priority": t.priority,
                        "status": t.status,
                        "created_at": t.created_at.isoformat(),
                    }
                )

            return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"查询失败: {str(e)}"}, ensure_ascii=False)


@tool
async def ticket_update(
    ticket_no: str,
    status: str | None = None,
    comment: str | None = None,
    priority: str | None = None,
) -> str:
    """更新技术支持工单的状态、优先级或添加备注。

    Args:
        ticket_no: 工单号
        status: 新状态 (open/in_progress/resolved/closed)
        comment: 添加的备注内容
        priority: 新优先级 (low/medium/high/critical)
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            result = await session.execute(
                select(SupportTicket).where(SupportTicket.ticket_no == ticket_no)
            )
            ticket = result.scalar_one_or_none()

            if not ticket:
                return json.dumps({"error": f"未找到工单: {ticket_no}"}, ensure_ascii=False)

            updates = []
            if status:
                ticket.status = status
                updates.append(f"状态更新为: {status}")
            if priority:
                ticket.priority = priority
                updates.append(f"优先级更新为: {priority}")
            if comment:
                ticket.description = f"{ticket.description}\n\n[客服备注 {datetime.now().strftime('%Y-%m-%d %H:%M')}] {comment}"
                updates.append("已添加备注")

            await session.commit()

            return json.dumps(
                {
                    "ticket_no": ticket_no,
                    "status": ticket.status,
                    "priority": ticket.priority,
                    "updated_fields": updates,
                    "message": f"工单更新成功: {'; '.join(updates)}",
                },
                ensure_ascii=False,
            )
    except Exception as e:
        return json.dumps({"error": f"更新工单失败: {str(e)}"}, ensure_ascii=False)


# ============================================================================
# GENERAL INFO TOOLS
# ============================================================================


@tool
async def faq_search(query: str, top_k: int = 3) -> str:
    """搜索常见问题解答。

    Args:
        query: 搜索问题
        top_k: 返回结果数量，默认3
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            search_pattern = f"%{query}%"
            stmt = (
                select(KnowledgeArticle)
                .where(
                    KnowledgeArticle.is_published,
                    KnowledgeArticle.category.in_(["general", "faq"]),
                    or_(
                        KnowledgeArticle.title.ilike(search_pattern),
                        KnowledgeArticle.content.ilike(search_pattern),
                    ),
                )
                .order_by(KnowledgeArticle.view_count.desc())
                .limit(top_k)
            )

            result = await session.execute(stmt)
            articles = result.scalars().all()

            if not articles:
                return json.dumps(
                    [{"question": "未找到相关FAQ", "answer": "请尝试其他关键词或联系人工客服"}],
                    ensure_ascii=False,
                )

            output = []
            for article in articles:
                title_match = query.lower() in article.title.lower()
                content_match = query.lower() in article.content.lower()
                relevance = 0.9 if title_match else (0.7 if content_match else 0.5)
                output.append(
                    {
                        "question": article.title,
                        "answer": article.content,
                        "category": article.category,
                        "relevance": relevance,
                    }
                )

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
            result = await session.execute(select(Customer).where(Customer.id == customer_id))
            customer = result.scalar_one_or_none()

            if not customer:
                return json.dumps({"error": f"未找到客户: {customer_id}"}, ensure_ascii=False)

            return json.dumps(
                {
                    "id": customer.id,
                    "name": customer.name,
                    "email": customer.email,
                    "phone": customer.phone,
                    "address": customer.address,
                    "vip_level": customer.vip_level,
                    "created_at": customer.created_at.isoformat(),
                },
                ensure_ascii=False,
            )
    except Exception as e:
        return json.dumps({"error": f"查询失败: {str(e)}"}, ensure_ascii=False)


# ============================================================================
# ADVANCED/Loyalty TOOLS
# ============================================================================


@tool
async def shipment_tracking(order_no: str) -> str:
    """查询订单的物流信息和追踪记录。

    Args:
        order_no: 订单号
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            order_result = await session.execute(select(Order).where(Order.order_no == order_no))
            order = order_result.scalar_one_or_none()

            if not order:
                return json.dumps({"error": f"未找到订单: {order_no}"}, ensure_ascii=False)

            shipment_result = await session.execute(
                select(Shipment).where(Shipment.order_id == order.id)
            )
            shipment = shipment_result.scalar_one_or_none()

            if not shipment:
                return json.dumps(
                    {
                        "order_no": order_no,
                        "order_status": order.status,
                        "message": "暂无物流信息，订单可能尚未发货",
                    },
                    ensure_ascii=False,
                )

            tracking_result = await session.execute(
                select(ShipmentTracking)
                .where(ShipmentTracking.shipment_id == shipment.id)
                .order_by(ShipmentTracking.event_time.desc())
            )
            events = tracking_result.scalars().all()

            data = {
                "order_no": order_no,
                "shipment_no": shipment.shipment_no,
                "carrier": shipment.carrier,
                "tracking_no": shipment.tracking_no,
                "status": shipment.status,
                "current_location": shipment.current_location,
                "shipped_at": shipment.shipped_at.isoformat() if shipment.shipped_at else None,
                "delivered_at": shipment.delivered_at.isoformat()
                if shipment.delivered_at
                else None,
                "estimated_delivery": shipment.estimated_delivery.isoformat()
                if shipment.estimated_delivery
                else None,
                "tracking_events": [
                    {
                        "time": e.event_time.isoformat(),
                        "type": e.event_type,
                        "location": e.location,
                        "description": e.description,
                    }
                    for e in events
                ],
            }

            return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"查询物流失败: {str(e)}"}, ensure_ascii=False)


@tool
async def loyalty_points_lookup(customer_id: str) -> str:
    """查询客户积分信息和积分历史。

    Args:
        customer_id: 客户ID
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            customer_result = await session.execute(
                select(Customer).where(Customer.id == customer_id)
            )
            customer = customer_result.scalar_one_or_none()

            if not customer:
                return json.dumps({"error": f"未找到客户: {customer_id}"}, ensure_ascii=False)

            points_result = await session.execute(
                select(LoyaltyPoints)
                .where(LoyaltyPoints.customer_id == customer_id)
                .order_by(LoyaltyPoints.created_at.desc())
                .limit(10)
            )
            points_history = points_result.scalars().all()

            total_earned = sum(p.points for p in points_history if p.points > 0)
            total_redeemed = sum(abs(p.points) for p in points_history if p.points < 0)

            data = {
                "customer_id": customer_id,
                "customer_name": customer.name,
                "current_points": customer.loyalty_points,
                "vip_level": customer.vip_level,
                "total_spent": float(customer.total_spent),
                "total_earned": total_earned,
                "total_redeemed": total_redeemed,
                "points_history": [
                    {
                        "points": p.points,
                        "balance": p.balance,
                        "type": p.type,
                        "description": p.description,
                        "created_at": p.created_at.isoformat(),
                    }
                    for p in points_history
                ],
            }

            return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"查询积分失败: {str(e)}"}, ensure_ascii=False)


@tool
async def customer_coupon_lookup(customer_id: str) -> str:
    """查询客户的优惠券信息。

    Args:
        customer_id: 客户ID
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            customer_result = await session.execute(
                select(Customer).where(Customer.id == customer_id)
            )
            customer = customer_result.scalar_one_or_none()

            if not customer:
                return json.dumps({"error": f"未找到客户: {customer_id}"}, ensure_ascii=False)

            coupon_result = await session.execute(
                select(CustomerCoupon, Coupon)
                .join(Coupon, CustomerCoupon.coupon_id == Coupon.id)
                .where(CustomerCoupon.customer_id == customer_id)
                .order_by(CustomerCoupon.created_at.desc())
            )
            coupons = coupon_result.all()

            data = {
                "customer_id": customer_id,
                "customer_name": customer.name,
                "vip_level": customer.vip_level,
                "coupons": {
                    "available": [],
                    "used": [],
                    "expired": [],
                },
            }

            now = datetime.now()
            for cc, coupon in coupons:
                coupon_info = {
                    "code": coupon.code,
                    "name": coupon.name,
                    "description": coupon.description,
                    "discount_type": coupon.discount_type,
                    "discount_value": float(coupon.discount_value),
                    "min_order_amount": float(coupon.min_order_amount),
                    "valid_until": coupon.valid_until.isoformat(),
                }

                if cc.is_used:
                    coupon_info["used_at"] = cc.used_at.isoformat() if cc.used_at else None
                    data["coupons"]["used"].append(coupon_info)
                elif coupon.valid_until < now or not coupon.is_active:
                    data["coupons"]["expired"].append(coupon_info)
                else:
                    data["coupons"]["available"].append(coupon_info)

            return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"查询优惠券失败: {str(e)}"}, ensure_ascii=False)


@tool
async def product_recommendation(
    category: str | None = None, price_range: str | None = None, limit: int = 3
) -> str:
    """根据条件推荐产品。

    Args:
        category: 产品类别（手表/手环/耳机/配件/家居）
        price_range: 价格范围（如 "0-500", "500-1000", "1000-2000", "2000+"）
        limit: 返回产品数量，默认3
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            query = select(Product).where(Product.is_active, Product.stock > 0)

            if category:
                query = query.where(Product.category == category)

            if price_range:
                if price_range == "0-500":
                    query = query.where(Product.price <= 500)
                elif price_range == "500-1000":
                    query = query.where(Product.price > 500, Product.price <= 1000)
                elif price_range == "1000-2000":
                    query = query.where(Product.price > 1000, Product.price <= 2000)
                elif price_range == "2000+":
                    query = query.where(Product.price > 2000)

            query = query.order_by(Product.rating.desc(), Product.review_count.desc())
            query = query.limit(limit)

            result = await session.execute(query)
            products = result.scalars().all()

            if not products:
                return json.dumps({"message": "未找到符合条件的产品"}, ensure_ascii=False)

            data = {
                "category": category,
                "price_range": price_range,
                "recommendations": [],
            }

            for p in products:
                data["recommendations"].append(
                    {
                        "sku": p.sku,
                        "name": p.name,
                        "description": p.description[:100] if p.description else "",
                        "category": p.category,
                        "price": float(p.price),
                        "rating": float(p.rating),
                        "review_count": p.review_count,
                        "stock": p.stock,
                        "brand": p.brand,
                    }
                )

            return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"推荐产品失败: {str(e)}"}, ensure_ascii=False)


@tool
async def customer_feedback_submit(
    customer_id: str, feedback_type: str, subject: str, content: str, rating: int | None = None
) -> str:
    """提交客户反馈。

    Args:
        customer_id: 客户ID
        feedback_type: 反馈类型 (complaint/suggestion/praise/question)
        subject: 反馈主题
        content: 反馈内容
        rating: 评分（1-5星），可选
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            feedback = CustomerFeedback(
                customer_id=customer_id,
                type=feedback_type,
                subject=subject,
                content=content,
                rating=rating,
                status="pending",
            )
            session.add(feedback)
            await session.commit()

            return json.dumps(
                {
                    "feedback_id": feedback.id,
                    "customer_id": customer_id,
                    "type": feedback_type,
                    "subject": subject,
                    "status": "pending",
                    "message": "反馈已提交，我们会尽快处理并回复您",
                },
                ensure_ascii=False,
            )
    except Exception as e:
        return json.dumps({"error": f"提交反馈失败: {str(e)}"}, ensure_ascii=False)


@tool
async def loyalty_points_redeem(customer_id: str, points: int, coupon_id: str | None = None) -> str:
    """兑换客户积分。

    Args:
        customer_id: 客户ID
        points: 要兑换的积分数量
        coupon_id: 可选的兑换优惠券ID
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            customer_result = await session.execute(
                select(Customer).where(Customer.id == customer_id)
            )
            customer = customer_result.scalar_one_or_none()

            if not customer:
                return json.dumps({"error": f"未找到客户: {customer_id}"}, ensure_ascii=False)

            if customer.loyalty_points < points:
                return json.dumps(
                    {"error": f"积分不足。当前积分: {customer.loyalty_points}，需要: {points}"},
                    ensure_ascii=False,
                )

            redeem_value = points / 100
            points_record = LoyaltyPoints(
                customer_id=customer_id,
                points=-points,
                balance=customer.loyalty_points - points,
                type="redeem",
                description=f"积分兑换: -{points}积分 (价值约¥{redeem_value})",
            )
            session.add(points_record)

            customer.loyalty_points -= points

            coupon_message = ""
            if coupon_id:
                coupon_result = await session.execute(
                    select(Coupon).where(Coupon.id == coupon_id, Coupon.is_active)
                )
                coupon = coupon_result.scalar_one_or_none()
                if coupon:
                    cc = CustomerCoupon(
                        customer_id=customer_id,
                        coupon_id=coupon.id,
                    )
                    session.add(cc)
                    coupon_message = f"，已发放优惠券: {coupon.code}"

            await session.commit()

            return json.dumps(
                {
                    "customer_id": customer_id,
                    "redeemed_points": points,
                    "redeem_value": redeem_value,
                    "remaining_points": customer.loyalty_points,
                    "message": f"积分兑换成功: -{points}积分 (价值约¥{redeem_value}){coupon_message}",
                },
                ensure_ascii=False,
            )
    except Exception as e:
        return json.dumps({"error": f"积分兑换失败: {str(e)}"}, ensure_ascii=False)


@tool
async def coupon_apply(customer_id: str, coupon_code: str, order_no: str) -> str:
    """使用优惠券。

    Args:
        customer_id: 客户ID
        coupon_code: 优惠券代码
        order_no: 订单号
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            order_result = await session.execute(select(Order).where(Order.order_no == order_no))
            order = order_result.scalar_one_or_none()

            if not order:
                return json.dumps({"error": f"未找到订单: {order_no}"}, ensure_ascii=False)

            coupon_result = await session.execute(
                select(Coupon).where(Coupon.code == coupon_code, Coupon.is_active)
            )
            coupon = coupon_result.scalar_one_or_none()

            if not coupon:
                return json.dumps({"error": f"无效的优惠券代码: {coupon_code}"}, ensure_ascii=False)

            if coupon.valid_until < datetime.now():
                return json.dumps({"error": "优惠券已过期"}, ensure_ascii=False)

            customer_coupon_result = await session.execute(
                select(CustomerCoupon).where(
                    CustomerCoupon.customer_id == customer_id,
                    CustomerCoupon.coupon_id == coupon.id,
                    not CustomerCoupon.is_used,
                )
            )
            customer_coupon = customer_coupon_result.scalar_one_or_none()

            if not customer_coupon:
                return json.dumps({"error": "该优惠券不可用或已被使用"}, ensure_ascii=False)

            if float(order.total_amount) < float(coupon.min_order_amount):
                return json.dumps(
                    {"error": f"订单金额不满足优惠券使用条件（需满¥{coupon.min_order_amount}）"},
                    ensure_ascii=False,
                )

            discount_amount = float(coupon.discount_value)
            if coupon.discount_type == "percentage":
                discount_amount = float(order.total_amount) * (discount_amount / 100)

            customer_coupon.is_used = True
            customer_coupon.used_at = datetime.now()
            customer_coupon.order_id = order.id

            await session.commit()

            return json.dumps(
                {
                    "coupon_code": coupon_code,
                    "order_no": order_no,
                    "discount_type": coupon.discount_type,
                    "discount_value": float(coupon.discount_value),
                    "discount_amount": min(discount_amount, float(order.total_amount)),
                    "message": f"优惠券 {coupon_code} 已成功使用，减免 ¥{discount_amount:.2f}",
                },
                ensure_ascii=False,
            )
    except Exception as e:
        return json.dumps({"error": f"使用优惠券失败: {str(e)}"}, ensure_ascii=False)


# ============================================================================
# ALL TOOLS LIST
# ============================================================================

ALL_TOOLS = [
    # Order management
    order_lookup,
    cancel_order,
    create_order,
    get_customer_address,
    # Product
    search_products,
    get_product_info,
    product_recommendation,
    # Refund
    refund_eligibility,
    process_refund,
    refund_status_lookup,
    # Billing
    invoice_lookup,
    payment_history,
    billing_summary,
    order_payment_match,
    # Technical
    knowledge_search,
    ticket_create,
    ticket_lookup,
    ticket_update,
    # General
    faq_search,
    company_info,
    customer_info,
    shipment_tracking,
    loyalty_points_lookup,
    customer_coupon_lookup,
    customer_feedback_submit,
    loyalty_points_redeem,
    coupon_apply,
]
