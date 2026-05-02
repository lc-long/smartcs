from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.v1.auth import get_current_user, require_role
from backend.app.core.database import get_db_session
from backend.app.models.db.ecommerce import (
    Customer,
    CustomerFeedback,
    Order,
    OrderItem,
    Payment,
    Product,
    ProductReview,
    Refund,
    Shipment,
    SupportTicket,
)
from backend.app.models.db.user import User

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/dashboard")
async def get_dashboard_stats(
    current_user: User = Depends(require_role("admin", "agent")),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """获取仪表盘统计数据"""
    try:
        # 总客户数
        result = await session.execute(select(func.count(Customer.id)))
        total_customers = result.scalar() or 0

        # 总订单数
        result = await session.execute(select(func.count(Order.id)))
        total_orders = result.scalar() or 0

        # 总销售额
        result = await session.execute(
            select(func.sum(Order.final_amount)).where(Order.status != "cancelled")
        )
        total_revenue = float(result.scalar() or 0)

        # 今日订单
        today = datetime.now().date()
        result = await session.execute(
            select(func.count(Order.id)).where(
                func.date(Order.created_at) == today
            )
        )
        today_orders = result.scalar() or 0

        # 待处理工单
        result = await session.execute(
            select(func.count(SupportTicket.id)).where(
                SupportTicket.status.in_(["open", "in_progress"])
            )
        )
        pending_tickets = result.scalar() or 0

        # 待处理退款
        result = await session.execute(
            select(func.count(Refund.id)).where(Refund.status == "pending")
        )
        pending_refunds = result.scalar() or 0

        # 平均订单金额
        result = await session.execute(
            select(func.avg(Order.final_amount)).where(Order.status != "cancelled")
        )
        avg_order_amount = float(result.scalar() or 0)

        # 客户满意度（基于评价）
        result = await session.execute(
            select(func.avg(ProductReview.rating))
        )
        avg_rating = float(result.scalar() or 0)

        # 最近7天订单趋势
        seven_days_ago = datetime.now() - timedelta(days=7)
        result = await session.execute(
            select(
                func.date(Order.created_at).label("date"),
                func.count(Order.id).label("count"),
                func.sum(Order.final_amount).label("amount"),
            )
            .where(Order.created_at >= seven_days_ago)
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at))
        )
        order_trend = [
            {
                "date": str(row.date),
                "count": row.count,
                "amount": float(row.amount or 0),
            }
            for row in result.all()
        ]

        # 订单状态分布
        result = await session.execute(
            select(
                Order.status,
                func.count(Order.id).label("count"),
            ).group_by(Order.status)
        )
        order_status_dist = {row.status: row.count for row in result.all()}

        # 热销商品 Top 5
        result = await session.execute(
            select(
                OrderItem.product_name,
                func.sum(OrderItem.quantity).label("total_qty"),
                func.sum(OrderItem.subtotal).label("total_amount"),
            )
            .group_by(OrderItem.product_name)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(5)
        )
        top_products = [
            {
                "name": row.product_name,
                "quantity": int(row.total_qty),
                "amount": float(row.total_amount),
            }
            for row in result.all()
        ]

        return {
            "summary": {
                "total_customers": total_customers,
                "total_orders": total_orders,
                "total_revenue": total_revenue,
                "today_orders": today_orders,
                "pending_tickets": pending_tickets,
                "pending_refunds": pending_refunds,
                "avg_order_amount": round(avg_order_amount, 2),
                "avg_rating": round(avg_rating, 2),
            },
            "order_trend": order_trend,
            "order_status_distribution": order_status_dist,
            "top_products": top_products,
        }
    except Exception as e:
        logger.exception("dashboard_stats_error")
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")


@router.get("/agents/performance")
async def get_agent_performance(
    days: int = 30,
    current_user: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """获取客服绩效统计"""
    try:
        start_date = datetime.now() - timedelta(days=days)

        # 工单处理统计
        result = await session.execute(
            select(
                SupportTicket.assigned_to,
                func.count(SupportTicket.id).label("total"),
                func.sum(
                    case(
                        (SupportTicket.status == "resolved", 1),
                        else_=0,
                    )
                ).label("resolved"),
                func.sum(
                    case(
                        (SupportTicket.status == "in_progress", 1),
                        else_=0,
                    )
                ).label("in_progress"),
            )
            .where(SupportTicket.created_at >= start_date)
            .where(SupportTicket.assigned_to.isnot(None))
            .group_by(SupportTicket.assigned_to)
        )
        agent_tickets = []
        for row in result.all():
            resolved = int(row.resolved or 0)
            total = int(row.total or 0)
            agent_tickets.append({
                "agent": row.assigned_to,
                "total_tickets": total,
                "resolved": resolved,
                "in_progress": int(row.in_progress or 0),
                "resolution_rate": round(resolved / total * 100, 1) if total > 0 else 0,
            })

        # 退款审批统计
        result = await session.execute(
            select(
                Refund.approved_by,
                func.count(Refund.id).label("total"),
                func.sum(
                    case(
                        (Refund.status == "approved", 1),
                        else_=0,
                    )
                ).label("approved"),
                func.sum(
                    case(
                        (Refund.status == "rejected", 1),
                        else_=0,
                    )
                ).label("rejected"),
            )
            .where(Refund.created_at >= start_date)
            .where(Refund.approved_by.isnot(None))
            .group_by(Refund.approved_by)
        )
        agent_refunds = []
        for row in result.all():
            agent_refunds.append({
                "agent": row.approved_by,
                "total_reviews": int(row.total or 0),
                "approved": int(row.approved or 0),
                "rejected": int(row.rejected or 0),
            })

        # 总体统计
        result = await session.execute(
            select(
                func.count(SupportTicket.id).label("total_tickets"),
                func.sum(
                    case(
                        (SupportTicket.status == "resolved", 1),
                        else_=0,
                    )
                ).label("resolved_tickets"),
            )
            .where(SupportTicket.created_at >= start_date)
        )
        row = result.one()
        total_tickets = int(row.total_tickets or 0)
        resolved_tickets = int(row.resolved_tickets or 0)

        return {
            "period_days": days,
            "summary": {
                "total_tickets": total_tickets,
                "resolved_tickets": resolved_tickets,
                "resolution_rate": round(resolved_tickets / total_tickets * 100, 1) if total_tickets > 0 else 0,
            },
            "agent_ticket_stats": agent_tickets,
            "agent_refund_stats": agent_refunds,
        }
    except Exception as e:
        logger.exception("agent_performance_error")
        raise HTTPException(status_code=500, detail=f"获取绩效数据失败: {str(e)}")


@router.get("/satisfaction")
async def get_customer_satisfaction(
    days: int = 30,
    current_user: User = Depends(require_role("admin", "agent")),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """获取客户满意度统计"""
    try:
        start_date = datetime.now() - timedelta(days=days)

        # 评价统计
        result = await session.execute(
            select(
                func.count(ProductReview.id).label("total"),
                func.avg(ProductReview.rating).label("avg_rating"),
                func.sum(case((ProductReview.rating >= 4, 1), else_=0)).label("positive"),
                func.sum(case((ProductReview.rating == 3, 1), else_=0)).label("neutral"),
                func.sum(case((ProductReview.rating <= 2, 1), else_=0)).label("negative"),
            )
            .where(ProductReview.created_at >= start_date)
        )
        review_stats = result.one()

        # 评分分布
        result = await session.execute(
            select(
                ProductReview.rating,
                func.count(ProductReview.id).label("count"),
            )
            .where(ProductReview.created_at >= start_date)
            .group_by(ProductReview.rating)
            .order_by(ProductReview.rating)
        )
        rating_dist = {row.rating: row.count for row in result.all()}

        # 反馈统计
        result = await session.execute(
            select(
                CustomerFeedback.type,
                func.count(CustomerFeedback.id).label("count"),
            )
            .where(CustomerFeedback.created_at >= start_date)
            .group_by(CustomerFeedback.type)
        )
        feedback_dist = {row.type: row.count for row in result.all()}

        # 反馈状态统计
        result = await session.execute(
            select(
                CustomerFeedback.status,
                func.count(CustomerFeedback.id).label("count"),
            )
            .where(CustomerFeedback.created_at >= start_date)
            .group_by(CustomerFeedback.status)
        )
        feedback_status = {row.status: row.count for row in result.all()}

        # 工单分类统计
        result = await session.execute(
            select(
                SupportTicket.category,
                func.count(SupportTicket.id).label("count"),
            )
            .where(SupportTicket.created_at >= start_date)
            .group_by(SupportTicket.category)
        )
        ticket_category = {row.category: row.count for row in result.all()}

        # 工单优先级统计
        result = await session.execute(
            select(
                SupportTicket.priority,
                func.count(SupportTicket.id).label("count"),
            )
            .where(SupportTicket.created_at >= start_date)
            .group_by(SupportTicket.priority)
        )
        ticket_priority = {row.priority: row.count for row in result.all()}

        total_reviews = int(review_stats.total or 0)
        positive = int(review_stats.positive or 0)
        negative = int(review_stats.negative or 0)

        return {
            "period_days": days,
            "review_summary": {
                "total_reviews": total_reviews,
                "avg_rating": round(float(review_stats.avg_rating or 0), 2),
                "positive_rate": round(positive / total_reviews * 100, 1) if total_reviews > 0 else 0,
                "negative_rate": round(negative / total_reviews * 100, 1) if total_reviews > 0 else 0,
            },
            "rating_distribution": rating_dist,
            "feedback_distribution": feedback_dist,
            "feedback_status": feedback_status,
            "ticket_category_distribution": ticket_category,
            "ticket_priority_distribution": ticket_priority,
        }
    except Exception as e:
        logger.exception("satisfaction_stats_error")
        raise HTTPException(status_code=500, detail=f"获取满意度数据失败: {str(e)}")


@router.get("/products/analytics")
async def get_product_analytics(
    current_user: User = Depends(require_role("admin", "agent")),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """获取商品分析数据"""
    try:
        # 商品销售排行
        result = await session.execute(
            select(
                OrderItem.product_name,
                func.count(OrderItem.id).label("order_count"),
                func.sum(OrderItem.quantity).label("total_qty"),
                func.sum(OrderItem.subtotal).label("total_amount"),
            )
            .group_by(OrderItem.product_name)
            .order_by(func.sum(OrderItem.subtotal).desc())
        )
        product_sales = [
            {
                "name": row.product_name,
                "order_count": row.order_count,
                "quantity": int(row.total_qty),
                "amount": float(row.total_amount),
            }
            for row in result.all()
        ]

        # 商品评价排行
        result = await session.execute(
            select(
                Product.name,
                Product.rating,
                Product.review_count,
            )
            .where(Product.is_active == True)
            .order_by(Product.rating.desc())
            .limit(10)
        )
        product_ratings = [
            {
                "name": row.name,
                "rating": float(row.rating),
                "review_count": row.review_count,
            }
            for row in result.all()
        ]

        # 库存预警（库存低于50）
        result = await session.execute(
            select(Product)
            .where(Product.is_active == True, Product.stock < 50)
            .order_by(Product.stock.asc())
        )
        low_stock = [
            {
                "sku": p.sku,
                "name": p.name,
                "stock": p.stock,
                "category": p.category,
            }
            for p in result.scalars().all()
        ]

        # 分类销售统计
        result = await session.execute(
            select(
                Product.category,
                func.sum(OrderItem.subtotal).label("amount"),
                func.sum(OrderItem.quantity).label("quantity"),
            )
            .join(Product, OrderItem.product_id == Product.id)
            .group_by(Product.category)
        )
        category_sales = [
            {
                "category": row.category,
                "amount": float(row.amount),
                "quantity": int(row.quantity),
            }
            for row in result.all()
        ]

        return {
            "product_sales_ranking": product_sales,
            "product_rating_ranking": product_ratings,
            "low_stock_alerts": low_stock,
            "category_sales": category_sales,
        }
    except Exception as e:
        logger.exception("product_analytics_error")
        raise HTTPException(status_code=500, detail=f"获取商品分析失败: {str(e)}")


@router.get("/logistics")
async def get_logistics_stats(
    current_user: User = Depends(require_role("admin", "agent")),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """获取物流统计数据"""
    try:
        # 物流状态分布
        result = await session.execute(
            select(
                Shipment.status,
                func.count(Shipment.id).label("count"),
            ).group_by(Shipment.status)
        )
        status_dist = {row.status: row.count for row in result.all()}

        # 快递公司分布
        result = await session.execute(
            select(
                Shipment.carrier,
                func.count(Shipment.id).label("count"),
            ).group_by(Shipment.carrier)
        )
        carrier_dist = {row.carrier: row.count for row in result.all()}

        # 平均配送时间（已送达的订单）
        result = await session.execute(
            select(
                func.avg(
                    func.extract("epoch", Shipment.delivered_at - Shipment.shipped_at) / 86400
                ).label("avg_days")
            ).where(
                Shipment.status == "delivered",
                Shipment.delivered_at.isnot(None),
                Shipment.shipped_at.isnot(None),
            )
        )
        avg_delivery_days = round(float(result.scalar() or 0), 1)

        # 运输中订单数
        result = await session.execute(
            select(func.count(Shipment.id)).where(
                Shipment.status.in_(["shipped", "in_transit"])
            )
        )
        in_transit_count = result.scalar() or 0

        return {
            "status_distribution": status_dist,
            "carrier_distribution": carrier_dist,
            "avg_delivery_days": avg_delivery_days,
            "in_transit_count": in_transit_count,
        }
    except Exception as e:
        logger.exception("logistics_stats_error")
        raise HTTPException(status_code=500, detail=f"获取物流统计失败: {str(e)}")
