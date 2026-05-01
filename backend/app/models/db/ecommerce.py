from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class Product(Base):
    """商品表"""
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warranty_months: Mapped[int] = mapped_column(Integer, nullable=False, default=12)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    weight: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False, default=0)
    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    reviews: Mapped[list[ProductReview]] = relationship(back_populates="product")

    def __repr__(self):
        return f"<Product {self.sku} {self.name}>"


class Customer(Base):
    """客户表"""
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    vip_level: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")
    loyalty_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_spent: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    registration_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    orders: Mapped[list[Order]] = relationship(back_populates="customer")
    reviews: Mapped[list[ProductReview]] = relationship(back_populates="customer")
    feedback: Mapped[list[CustomerFeedback]] = relationship(back_populates="customer")
    coupons: Mapped[list[CustomerCoupon]] = relationship(back_populates="customer")

    def __repr__(self):
        return f"<Customer {self.name} {self.email}>"


class Order(Base):
    """订单表"""
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    order_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    shipping_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    final_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    coupon_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    shipping_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer: Mapped[Customer] = relationship(back_populates="orders")
    items: Mapped[list[OrderItem]] = relationship(back_populates="order")
    payments: Mapped[list[Payment]] = relationship(back_populates="order")
    refunds: Mapped[list[Refund]] = relationship(back_populates="order")
    shipments: Mapped[list[Shipment]] = relationship(back_populates="order")
    status_history: Mapped[list[OrderStatusHistory]] = relationship(back_populates="order")

    def __repr__(self):
        return f"<Order {self.order_no} status={self.status}>"


class OrderItem(Base):
    """订单商品表"""
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.id"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), nullable=False)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped[Order] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()

    def __repr__(self):
        return f"<OrderItem {self.product_name} x{self.quantity}>"


class Invoice(Base):
    """发票/账单表"""
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    invoice_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    order_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("orders.id"), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Invoice {self.invoice_no} amount={self.amount}>"


class Payment(Base):
    """支付记录表"""
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    payment_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.id"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    transaction_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order: Mapped[Order] = relationship(back_populates="payments")

    def __repr__(self):
        return f"<Payment {self.payment_no} amount={self.amount}>"


class Refund(Base):
    """退款记录表"""
    __tablename__ = "refunds"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    refund_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.id"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    approved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order: Mapped[Order] = relationship(back_populates="refunds")

    def __repr__(self):
        return f"<Refund {self.refund_no} amount={self.amount}>"


class SupportTicket(Base):
    """客服工单表"""
    __tablename__ = "support_tickets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    ticket_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    order_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("orders.id"), nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open", index=True)
    assigned_to: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<SupportTicket {self.ticket_no} {self.title}>"


class KnowledgeArticle(Base):
    """知识库文章表"""
    __tablename__ = "knowledge_articles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<KnowledgeArticle {self.title}>"


class Shipment(Base):
    """物流追踪表"""
    __tablename__ = "shipments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    shipment_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.id"), nullable=False, index=True)
    carrier: Mapped[str] = mapped_column(String(50), nullable=False)  # 顺丰/圆通/中通/韵达
    tracking_no: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending/shipped/in_transit/delivered
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estimated_delivery: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    order: Mapped[Order] = relationship(back_populates="shipments")
    tracking_events: Mapped[list[ShipmentTracking]] = relationship(back_populates="shipment")

    def __repr__(self):
        return f"<Shipment {self.shipment_no} {self.carrier}>"


class ShipmentTracking(Base):
    """物流追踪事件表"""
    __tablename__ = "shipment_tracking"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    shipment_id: Mapped[str] = mapped_column(String(36), ForeignKey("shipments.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # picked_up/in_transit/out_for_delivery/delivered/exception
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    shipment: Mapped[Shipment] = relationship(back_populates="tracking_events")

    def __repr__(self):
        return f"<ShipmentTracking {self.event_type} at {self.location}>"


class ProductReview(Base):
    """产品评价表"""
    __tablename__ = "product_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    order_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("orders.id"), nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    helpful_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped[Product] = relationship(back_populates="reviews")
    customer: Mapped[Customer] = relationship(back_populates="reviews")

    def __repr__(self):
        return f"<ProductReview rating={self.rating}>"


class LoyaltyPoints(Base):
    """积分记录表"""
    __tablename__ = "loyalty_points"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    points: Mapped[int] = mapped_column(Integer, nullable=False)  # 正数增加，负数减少
    balance: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # earned/redeemed/expired/adjusted
    description: Mapped[str] = mapped_column(Text, nullable=False)
    reference_id: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 关联订单号或活动ID
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<LoyaltyPoints {self.points} ({self.type})>"


class Coupon(Base):
    """优惠券表"""
    __tablename__ = "coupons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False)  # percentage/fixed
    discount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    min_order_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    max_discount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    usage_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Coupon {self.code} {self.discount_value}>"


class CustomerCoupon(Base):
    """客户优惠券关联表"""
    __tablename__ = "customer_coupons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    coupon_id: Mapped[str] = mapped_column(String(36), ForeignKey("coupons.id"), nullable=False, index=True)
    is_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    order_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("orders.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    customer: Mapped[Customer] = relationship(back_populates="coupons")
    coupon: Mapped[Coupon] = relationship()

    def __repr__(self):
        return f"<CustomerCoupon customer={self.customer_id}>"


class OrderStatusHistory(Base):
    """订单状态历史表"""
    __tablename__ = "order_status_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.id"), nullable=False, index=True)
    old_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_by: Mapped[str] = mapped_column(String(100), nullable=False)  # system/agent/admin
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order: Mapped[Order] = relationship(back_populates="status_history")

    def __repr__(self):
        return f"<OrderStatusHistory {self.old_status} -> {self.new_status}>"


class CustomerFeedback(Base):
    """客户反馈表"""
    __tablename__ = "customer_feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    order_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("orders.id"), nullable=True)
    ticket_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("support_tickets.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # complaint/suggestion/praise/question
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending/in_review/resolved/closed
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    responded_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    customer: Mapped[Customer] = relationship(back_populates="feedback")

    def __repr__(self):
        return f"<CustomerFeedback {self.type} {self.subject}>"
