from __future__ import annotations

import json
from datetime import datetime

from langchain_core.tools import tool
from sqlalchemy import select

from backend.app.core.database import get_session_factory
from backend.app.models.db.ecommerce import (
    Coupon,
    Customer,
    CustomerCoupon,
    CustomerFeedback,
    LoyaltyPoints,
    Order,
    Product,
    ProductReview,
    Shipment,
    ShipmentTracking,
)


@tool
async def shipment_tracking(order_no: str) -> str:
    """查询订单的物流信息和追踪记录。

    Args:
        order_no: 订单号
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            # 查询订单
            order_result = await session.execute(
                select(Order).where(Order.order_no == order_no)
            )
            order = order_result.scalar_one_or_none()

            if not order:
                return json.dumps({"error": f"未找到订单: {order_no}"}, ensure_ascii=False)

            # 查询物流
            shipment_result = await session.execute(
                select(Shipment).where(Shipment.order_id == order.id)
            )
            shipment = shipment_result.scalar_one_or_none()

            if not shipment:
                return json.dumps({
                    "order_no": order_no,
                    "order_status": order.status,
                    "message": "暂无物流信息，订单可能尚未发货"
                }, ensure_ascii=False)

            # 查询追踪事件
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
                "delivered_at": shipment.delivered_at.isoformat() if shipment.delivered_at else None,
                "estimated_delivery": shipment.estimated_delivery.isoformat() if shipment.estimated_delivery else None,
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
async def product_review_lookup(product_name: str | None = None, product_id: str | None = None, limit: int = 5) -> str:
    """查询产品评价。

    Args:
        product_name: 产品名称（可模糊匹配）
        product_id: 产品ID（精确匹配）
        limit: 返回评价数量，默认5
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            # 先查询产品
            if product_id:
                product_result = await session.execute(
                    select(Product).where(Product.id == product_id)
                )
            elif product_name:
                product_result = await session.execute(
                    select(Product).where(Product.name.contains(product_name))
                )
            else:
                return json.dumps({"error": "请提供产品名称或产品ID"}, ensure_ascii=False)

            product = product_result.scalar_one_or_none()
            if not product:
                return json.dumps({"error": f"未找到产品: {product_name or product_id}"}, ensure_ascii=False)

            # 查询评价
            review_result = await session.execute(
                select(ProductReview)
                .where(ProductReview.product_id == product.id)
                .order_by(ProductReview.created_at.desc())
                .limit(limit)
            )
            reviews = review_result.scalars().all()

            # 查询客户信息
            data = {
                "product_name": product.name,
                "product_id": product.id,
                "rating": float(product.rating),
                "review_count": product.review_count,
                "reviews": [],
            }

            for review in reviews:
                customer_result = await session.execute(
                    select(Customer).where(Customer.id == review.customer_id)
                )
                customer = customer_result.scalar_one_or_none()
                customer_name = customer.name if customer and not review.is_anonymous else "匿名用户"

                data["reviews"].append({
                    "rating": review.rating,
                    "title": review.title,
                    "content": review.content[:200],
                    "customer": customer_name,
                    "created_at": review.created_at.isoformat(),
                    "helpful_count": review.helpful_count,
                })

            return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"查询评价失败: {str(e)}"}, ensure_ascii=False)


@tool
async def loyalty_points_lookup(customer_id: str) -> str:
    """查询客户积分信息和积分历史。

    Args:
        customer_id: 客户ID
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            # 查询客户
            customer_result = await session.execute(
                select(Customer).where(Customer.id == customer_id)
            )
            customer = customer_result.scalar_one_or_none()

            if not customer:
                return json.dumps({"error": f"未找到客户: {customer_id}"}, ensure_ascii=False)

            # 查询积分记录
            points_result = await session.execute(
                select(LoyaltyPoints)
                .where(LoyaltyPoints.customer_id == customer_id)
                .order_by(LoyaltyPoints.created_at.desc())
                .limit(10)
            )
            points_history = points_result.scalars().all()

            # 计算积分统计
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
            # 查询客户
            customer_result = await session.execute(
                select(Customer).where(Customer.id == customer_id)
            )
            customer = customer_result.scalar_one_or_none()

            if not customer:
                return json.dumps({"error": f"未找到客户: {customer_id}"}, ensure_ascii=False)

            # 查询客户优惠券
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
async def product_recommendation(category: str | None = None, price_range: str | None = None, limit: int = 3) -> str:
    """根据条件推荐产品。

    Args:
        category: 产品类别（手表/手环/耳机/配件/家居）
        price_range: 价格范围（如 "0-500", "500-1000", "1000-2000", "2000+"）
        limit: 返回产品数量，默认3
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            query = select(Product).where(Product.is_active == True, Product.stock > 0)

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

            # 按评分和销量排序
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
                data["recommendations"].append({
                    "sku": p.sku,
                    "name": p.name,
                    "description": p.description[:100] if p.description else "",
                    "category": p.category,
                    "price": float(p.price),
                    "rating": float(p.rating),
                    "review_count": p.review_count,
                    "stock": p.stock,
                    "brand": p.brand,
                })

            return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"推荐产品失败: {str(e)}"}, ensure_ascii=False)


@tool
async def customer_feedback_lookup(customer_id: str | None = None, feedback_type: str | None = None, status: str | None = None) -> str:
    """查询客户反馈信息。

    Args:
        customer_id: 客户ID（可选）
        feedback_type: 反馈类型（complaint/suggestion/praise/question）
        status: 状态（pending/in_review/resolved/closed）
    """
    try:
        factory = get_session_factory()
        async with factory() as session:
            query = select(CustomerFeedback)

            if customer_id:
                query = query.where(CustomerFeedback.customer_id == customer_id)
            if feedback_type:
                query = query.where(CustomerFeedback.type == feedback_type)
            if status:
                query = query.where(CustomerFeedback.status == status)

            query = query.order_by(CustomerFeedback.created_at.desc()).limit(10)

            result = await session.execute(query)
            feedbacks = result.scalars().all()

            if not feedbacks:
                return json.dumps({"message": "暂无反馈记录"}, ensure_ascii=False)

            data = {"feedbacks": []}

            for f in feedbacks:
                # 查询客户信息
                customer_result = await session.execute(
                    select(Customer).where(Customer.id == f.customer_id)
                )
                customer = customer_result.scalar_one_or_none()

                data["feedbacks"].append({
                    "id": f.id,
                    "customer_name": customer.name if customer else "未知",
                    "type": f.type,
                    "category": f.category,
                    "subject": f.subject,
                    "content": f.content[:300],
                    "rating": f.rating,
                    "status": f.status,
                    "response": f.response,
                    "created_at": f.created_at.isoformat(),
                })

            return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"查询反馈失败: {str(e)}"}, ensure_ascii=False)


@tool
async def customer_feedback_submit(customer_id: str, feedback_type: str, subject: str, content: str, rating: int | None = None) -> str:
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

            return json.dumps({
                "feedback_id": feedback.id,
                "customer_id": customer_id,
                "type": feedback_type,
                "subject": subject,
                "status": "pending",
                "message": "反馈已提交，我们会尽快处理并回复您",
            }, ensure_ascii=False)
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
                return json.dumps({
                    "error": f"积分不足。当前积分: {customer.loyalty_points}，需要: {points}"
                }, ensure_ascii=False)

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
                    select(Coupon).where(Coupon.id == coupon_id, Coupon.is_active == True)
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

            return json.dumps({
                "customer_id": customer_id,
                "redeemed_points": points,
                "redeem_value": redeem_value,
                "remaining_points": customer.loyalty_points,
                "message": f"积分兑换成功: -{points}积分 (价值约¥{redeem_value}){coupon_message}",
            }, ensure_ascii=False)
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
            order_result = await session.execute(
                select(Order).where(Order.order_no == order_no)
            )
            order = order_result.scalar_one_or_none()

            if not order:
                return json.dumps({"error": f"未找到订单: {order_no}"}, ensure_ascii=False)

            coupon_result = await session.execute(
                select(Coupon).where(Coupon.code == coupon_code, Coupon.is_active == True)
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
                    CustomerCoupon.is_used == False,
                )
            )
            customer_coupon = customer_coupon_result.scalar_one_or_none()

            if not customer_coupon:
                return json.dumps({"error": "该优惠券不可用或已被使用"}, ensure_ascii=False)

            if float(order.total_amount) < float(coupon.min_order_amount):
                return json.dumps({
                    "error": f"订单金额不满足优惠券使用条件（需满¥{coupon.min_order_amount}）"
                }, ensure_ascii=False)

            discount_amount = float(coupon.discount_value)
            if coupon.discount_type == "percentage":
                discount_amount = float(order.total_amount) * (discount_amount / 100)

            customer_coupon.is_used = True
            customer_coupon.used_at = datetime.now()
            customer_coupon.order_id = order.id

            await session.commit()

            return json.dumps({
                "coupon_code": coupon_code,
                "order_no": order_no,
                "discount_type": coupon.discount_type,
                "discount_value": float(coupon.discount_value),
                "discount_amount": min(discount_amount, float(order.total_amount)),
                "message": f"优惠券 {coupon_code} 已成功使用，减免 ¥{discount_amount:.2f}",
            }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"使用优惠券失败: {str(e)}"}, ensure_ascii=False)
