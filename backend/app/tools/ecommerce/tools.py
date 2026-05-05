from __future__ import annotations

import json
import uuid
from datetime import datetime
from decimal import Decimal

import structlog
from langchain_core.tools import tool
from sqlalchemy import and_, or_, select

from backend.app.core.database import get_session_factory
from backend.app.models.db.ecommerce import Customer, Order, OrderItem, Product

logger = structlog.get_logger()


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
                return json.dumps(
                    {"success": False, "error": f"未找到客户: {customer_id}"}
                )

            product_result = await session.execute(
                select(Product).where(Product.id == product_id)
            )
            product = product_result.scalar_one_or_none()
            if not product:
                return json.dumps(
                    {"success": False, "error": f"未找到产品: {product_id}"}
                )

            if product.stock < quantity:
                return json.dumps({
                    "success": False,
                    "error": f"库存不足，当前库存: {product.stock}",
                })

            address = shipping_address or customer.address or "未设置"
            if not shipping_address and customer.address:
                address = customer.address

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
            return json.dumps({
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
            }, ensure_ascii=False)
    except Exception as e:
        return json.dumps(
            {"success": False, "error": f"创建订单失败: {str(e)}"}
        )


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
                return json.dumps(
                    {"success": False, "error": "订单不存在或无权取消"}
                )

            cancellable_statuses = ["pending", "confirmed", "processing"]
            if order.status not in cancellable_statuses:
                return json.dumps({
                    "success": False,
                    "error": f"当前订单状态为'{order.status}'，无法取消",
                })

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
            return json.dumps({
                "success": True,
                "message": f"订单 {order_no} 已成功取消",
                "order_no": order_no,
                "refund_status": "将在3-5个工作日内退款到原支付方式",
            }, ensure_ascii=False)
    except Exception as e:
        return json.dumps(
            {"success": False, "error": f"取消订单失败: {str(e)}"}
        )


@tool
async def get_customer_address(customer_id: str) -> str:
    """获取客户默认收货地址。

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
                return json.dumps(
                    {"success": False, "error": f"未找到客户: {customer_id}"}
                )

            return json.dumps({
                "success": True,
                "customer_id": customer_id,
                "name": customer.name,
                "address": customer.address or "未设置",
                "phone": customer.phone or "未设置",
            }, ensure_ascii=False)
    except Exception as e:
        return json.dumps(
            {"success": False, "error": f"查询失败: {str(e)}"}
        )


@tool
async def get_product_info(product_id: str) -> str:
    """获取产品信息。

    Args:
        product_id: 产品ID
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            result = await session.execute(
                select(Product).where(Product.id == product_id)
            )
            product = result.scalar_one_or_none()

            if not product:
                return json.dumps(
                    {"success": False, "error": f"未找到产品: {product_id}"}
                )

            return json.dumps({
                "success": True,
                "product_id": product.id,
                "name": product.name,
                "price": float(product.price),
                "stock": product.stock,
                "description": product.description or "",
            }, ensure_ascii=False)
    except Exception as e:
        return json.dumps(
            {"success": False, "error": f"查询失败: {str(e)}"}
        )


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
                return json.dumps({
                    "success": True,
                    "products": [],
                    "message": "未找到相关产品",
                }, ensure_ascii=False)

            output = []
            for p in products:
                output.append({
                    "product_id": p.id,
                    "name": p.name,
                    "price": float(p.price),
                    "stock": p.stock,
                    "category": p.category or "",
                })

            return json.dumps({
                "success": True,
                "products": output,
                "count": len(output),
            }, ensure_ascii=False)
    except Exception as e:
        return json.dumps(
            {"success": False, "error": f"搜索失败: {str(e)}"}
        )
