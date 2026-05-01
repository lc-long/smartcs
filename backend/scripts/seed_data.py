from __future__ import annotations

import asyncio
import json
import random
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.core.database import get_engine, init_db
from backend.app.models.db.ecommerce import (
    Customer,
    CustomerCoupon,
    CustomerFeedback,
    Coupon,
    Invoice,
    KnowledgeArticle,
    LoyaltyPoints,
    Order,
    OrderItem,
    OrderStatusHistory,
    Payment,
    Product,
    ProductReview,
    Refund,
    Shipment,
    ShipmentTracking,
    SupportTicket,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


# 生成随机日期
def random_date(start_days_ago=90, end_days_ago=0):
    days = random.randint(end_days_ago, start_days_ago)
    return datetime.now() - timedelta(days=days, hours=random.randint(0, 23), minutes=random.randint(0, 59))


async def seed_database():
    """填充测试数据"""
    engine = get_engine()

    # 先创建表
    await init_db()

    async with AsyncSession(engine) as session:
        # 清空现有数据
        tables = [
            "customer_feedback", "customer_coupons", "loyalty_points", "product_reviews",
            "shipment_tracking", "shipments", "order_status_history",
            "support_tickets", "knowledge_articles", "refunds", "payments",
            "invoices", "order_items", "orders", "coupons", "products", "customers"
        ]
        for table in tables:
            await session.execute(text(f"DELETE FROM {table}"))
        await session.commit()

        # ==================== 1. 创建商品 (15个) ====================
        products = [
            # 手表类
            Product(id="P001", sku="WATCH-PRO-001", name="智能手表Pro", description="高端智能手表，支持心率监测、GPS定位、NFC支付、血氧检测、ECG心电图", category="手表", price=Decimal("1999.00"), stock=100, warranty_months=24, brand="SmartWear", weight=Decimal("45.00"), rating=Decimal("4.5"), review_count=128),
            Product(id="P002", sku="WATCH-LITE-001", name="智能手表Lite", description="轻量级智能手表，支持运动追踪、消息通知、睡眠监测", category="手表", price=Decimal("999.00"), stock=200, warranty_months=12, brand="SmartWear", weight=Decimal("38.00"), rating=Decimal("4.2"), review_count=85),
            Product(id="P003", sku="WATCH-ULTRA-001", name="智能手表Ultra", description="专业运动手表，钛合金表壳，100米防水，支持多种运动模式", category="手表", price=Decimal("3999.00"), stock=50, warranty_months=24, brand="SmartWear", weight=Decimal("52.00"), rating=Decimal("4.8"), review_count=42),
            # 手环类
            Product(id="P004", sku="BAND-PRO-001", name="智能手环Pro", description="专业运动手环，支持心率、血氧、压力监测，50米防水", category="手环", price=Decimal("499.00"), stock=300, warranty_months=12, brand="SmartWear", weight=Decimal("25.00"), rating=Decimal("4.3"), review_count=256),
            Product(id="P005", sku="BAND-LITE-001", name="智能手环Lite", description="入门级运动手环，支持步数统计、睡眠监测、消息提醒", category="手环", price=Decimal("199.00"), stock=500, warranty_months=6, brand="SmartWear", weight=Decimal("20.00"), rating=Decimal("4.0"), review_count=380),
            # 耳机类
            Product(id="P006", sku="EARBUDS-PRO-001", name="降噪耳机Pro", description="主动降噪无线耳机，支持空间音频、多点连接、高清通话", category="耳机", price=Decimal("1299.00"), stock=150, warranty_months=12, brand="AudioMax", weight=Decimal("5.50"), rating=Decimal("4.6"), review_count=192),
            Product(id="P007", sku="EARBUDS-LITE-001", name="无线耳机Lite", description="轻便无线耳机，支持蓝牙5.0，续航8小时", category="耳机", price=Decimal("399.00"), stock=400, warranty_months=6, brand="AudioMax", weight=Decimal("4.20"), rating=Decimal("4.1"), review_count=315),
            Product(id="P008", sku="EARBUDS-SPORT-001", name="运动耳机Sport", description="防水运动耳机，耳挂式设计，IP67防水，适合跑步健身", category="耳机", price=Decimal("599.00"), stock=250, warranty_months=12, brand="AudioMax", weight=Decimal("6.00"), rating=Decimal("4.4"), review_count=168),
            # 配件类
            Product(id="P009", sku="CHARGER-001", name="无线充电器", description="15W无线快充，支持Qi协议，兼容多设备", category="配件", price=Decimal("149.00"), stock=1000, warranty_months=6, brand="SmartWear", weight=Decimal("85.00"), rating=Decimal("4.2"), review_count=420),
            Product(id="P010", sku="CHARGER-CAR-001", name="车载充电器", description="双USB快充车充，支持PD30W+QC18W", category="配件", price=Decimal("79.00"), stock=800, warranty_months=6, brand="SmartWear", weight=Decimal("45.00"), rating=Decimal("4.0"), review_count=156),
            Product(id="P011", sku="STRAP-001", name="表带套装", description="3条不同风格表带（硅胶/皮革/金属），适配智能手表系列", category="配件", price=Decimal("199.00"), stock=800, warranty_months=3, brand="SmartWear", weight=Decimal("60.00"), rating=Decimal("4.3"), review_count=89),
            Product(id="P012", sku="CASE-001", name="耳机保护套", description="硅胶保护套，防摔防刮，多色可选", category="配件", price=Decimal("49.00"), stock=2000, warranty_months=3, brand="AudioMax", weight=Decimal("20.00"), rating=Decimal("4.1"), review_count=230),
            Product(id="P013", sku="CABLE-001", name="磁吸充电线", description="磁吸设计，一碰即充，1.5米长度", category="配件", price=Decimal("69.00"), stock=1500, warranty_months=6, brand="SmartWear", weight=Decimal("35.00"), rating=Decimal("4.4"), review_count=178),
            # 智能家居类
            Product(id="P014", sku="SCALE-001", name="智能体脂秤", description="高精度传感器，支持16项身体指标，APP数据同步", category="家居", price=Decimal("299.00"), stock=300, warranty_months=12, brand="HomeSmart", weight=Decimal("1800.00"), rating=Decimal("4.5"), review_count=203),
            Product(id="P015", sku="LAMP-001", name="智能台灯", description="护眼台灯，支持色温亮度调节，语音控制", category="家居", price=Decimal("399.00"), stock=200, warranty_months=12, brand="HomeSmart", weight=Decimal("800.00"), rating=Decimal("4.6"), review_count=95),
        ]
        session.add_all(products)
        await session.commit()

        # ==================== 2. 创建客户 (10个) ====================
        customers = [
            Customer(id="C001", name="张三", email="zhangsan@example.com", phone="13800138001", address="北京市朝阳区建国路88号SOHO现代城A座2301", vip_level="gold", loyalty_points=5800, total_spent=Decimal("12580.00")),
            Customer(id="C002", name="李四", email="lisi@example.com", phone="13800138002", address="上海市浦东新区陆家嘴金融中心100号", vip_level="silver", loyalty_points=3200, total_spent=Decimal("6890.00")),
            Customer(id="C003", name="王五", email="wangwu@example.com", phone="13800138003", address="广州市天河区天河路385号太古汇", vip_level="normal", loyalty_points=1500, total_spent=Decimal("3200.00")),
            Customer(id="C004", name="赵六", email="zhaoliu@example.com", phone="13800138004", address="深圳市南山区科技园路1号深圳湾创业广场", vip_level="gold", loyalty_points=8900, total_spent=Decimal("25600.00")),
            Customer(id="C005", name="钱七", email="qianqi@example.com", phone="13800138005", address="杭州市西湖区文三路90号互联网大厦", vip_level="normal", loyalty_points=800, total_spent=Decimal("1800.00")),
            Customer(id="C006", name="孙八", email="sunba@example.com", phone="13800138006", address="成都市高新区天府大道中段530号", vip_level="silver", loyalty_points=2800, total_spent=Decimal("5600.00")),
            Customer(id="C007", name="周九", email="zhoujiu@example.com", phone="13800138007", address="武汉市洪山区关山大道465号光谷软件园", vip_level="normal", loyalty_points=500, total_spent=Decimal("1200.00")),
            Customer(id="C008", name="吴十", email="wushi@example.com", phone="13800138008", address="南京市雨花台区软件大道168号", vip_level="gold", loyalty_points=12000, total_spent=Decimal("38900.00")),
            Customer(id="C009", name="郑十一", email="zheng11@example.com", phone="13800138009", address="西安市高新区科技路创业广场C座", vip_level="normal", loyalty_points=200, total_spent=Decimal("600.00")),
            Customer(id="C010", name="冯十二", email="feng12@example.com", phone="13800138010", address="重庆市渝北区新牌坊大道1号", vip_level="silver", loyalty_points=4500, total_spent=Decimal("9800.00")),
        ]
        session.add_all(customers)
        await session.commit()

        # ==================== 3. 创建订单 (20个) ====================
        orders_data = [
            # C001 张三 的订单 (金卡会员，高消费)
            {"id": "O001", "order_no": "ORD-20260115-001", "customer_id": "C001", "status": "delivered", "total": 5997, "discount": 600, "shipping": 0, "final": 5397, "addr": "北京市朝阳区建国路88号SOHO现代城A座2301", "date": datetime(2026, 1, 15)},
            {"id": "O002", "order_no": "ORD-20260220-001", "customer_id": "C001", "status": "delivered", "total": 1999, "discount": 200, "shipping": 0, "final": 1799, "addr": "北京市朝阳区建国路88号SOHO现代城A座2301", "date": datetime(2026, 2, 20)},
            {"id": "O003", "order_no": "ORD-20260310-001", "customer_id": "C001", "status": "delivered", "total": 1299, "discount": 0, "shipping": 0, "final": 1299, "addr": "北京市朝阳区建国路88号SOHO现代城A座2301", "date": datetime(2026, 3, 10)},
            {"id": "O004", "order_no": "ORD-20260401-001", "customer_id": "C001", "status": "delivered", "total": 3298, "discount": 330, "shipping": 0, "final": 2968, "addr": "北京市朝阳区建国路88号SOHO现代城A座2301", "date": datetime(2026, 4, 1)},
            {"id": "O005", "order_no": "ORD-20260425-001", "customer_id": "C001", "status": "delivered", "total": 1999, "discount": 0, "shipping": 0, "final": 1999, "addr": "北京市朝阳区建国路88号SOHO现代城A座2301", "date": datetime(2026, 4, 25)},
            # C002 李四 的订单
            {"id": "O006", "order_no": "ORD-20260205-001", "customer_id": "C002", "status": "delivered", "total": 1499, "discount": 75, "shipping": 0, "final": 1424, "addr": "上海市浦东新区陆家嘴金融中心100号", "date": datetime(2026, 2, 5)},
            {"id": "O007", "order_no": "ORD-20260315-001", "customer_id": "C002", "status": "delivered", "total": 598, "discount": 0, "shipping": 10, "final": 608, "addr": "上海市浦东新区陆家嘴金融中心100号", "date": datetime(2026, 3, 15)},
            {"id": "O008", "order_no": "ORD-20260410-001", "customer_id": "C002", "status": "shipped", "total": 3999, "discount": 400, "shipping": 0, "final": 3599, "addr": "上海市浦东新区陆家嘴金融中心100号", "date": datetime(2026, 4, 10)},
            {"id": "O009", "order_no": "ORD-20260428-001", "customer_id": "C002", "status": "processing", "total": 1299, "discount": 0, "shipping": 0, "final": 1299, "addr": "上海市浦东新区陆家嘴金融中心100号", "date": datetime(2026, 4, 28)},
            # C003 王五 的订单
            {"id": "O010", "order_no": "ORD-20260301-001", "customer_id": "C003", "status": "delivered", "total": 499, "discount": 0, "shipping": 10, "final": 509, "addr": "广州市天河区天河路385号太古汇", "date": datetime(2026, 3, 1)},
            {"id": "O011", "order_no": "ORD-20260405-001", "customer_id": "C003", "status": "pending", "total": 598, "discount": 0, "shipping": 0, "final": 598, "addr": "广州市天河区天河路385号太古汇", "date": datetime(2026, 4, 5)},
            # C004 赵六 的订单 (金卡会员，高消费)
            {"id": "O012", "order_no": "ORD-20260120-001", "customer_id": "C004", "status": "delivered", "total": 7996, "discount": 800, "shipping": 0, "final": 7196, "addr": "深圳市南山区科技园路1号深圳湾创业广场", "date": datetime(2026, 1, 20)},
            {"id": "O013", "order_no": "ORD-20260228-001", "customer_id": "C004", "status": "delivered", "total": 2498, "discount": 250, "shipping": 0, "final": 2248, "addr": "深圳市南山区科技园路1号深圳湾创业广场", "date": datetime(2026, 2, 28)},
            {"id": "O014", "order_no": "ORD-20260320-001", "customer_id": "C004", "status": "delivered", "total": 1299, "discount": 0, "shipping": 0, "final": 1299, "addr": "深圳市南山区科技园路1号深圳湾创业广场", "date": datetime(2026, 3, 20)},
            {"id": "O015", "order_no": "ORD-20260415-001", "customer_id": "C004", "status": "delivered", "total": 3999, "discount": 400, "shipping": 0, "final": 3599, "addr": "深圳市南山区科技园路1号深圳湾创业广场", "date": datetime(2026, 4, 15)},
            # C005 钱七 的订单
            {"id": "O016", "order_no": "ORD-20260325-001", "customer_id": "C005", "status": "cancelled", "total": 399, "discount": 0, "shipping": 10, "final": 409, "addr": "杭州市西湖区文三路90号互联网大厦", "date": datetime(2026, 3, 25)},
            {"id": "O017", "order_no": "ORD-20260418-001", "customer_id": "C005", "status": "delivered", "total": 199, "discount": 0, "shipping": 10, "final": 209, "addr": "杭州市西湖区文三路90号互联网大厦", "date": datetime(2026, 4, 18)},
            # C006-C010 的订单
            {"id": "O018", "order_no": "ORD-20260402-002", "customer_id": "C006", "status": "delivered", "total": 1299, "discount": 130, "shipping": 0, "final": 1169, "addr": "成都市高新区天府大道中段530号", "date": datetime(2026, 4, 2)},
            {"id": "O019", "order_no": "ORD-20260412-001", "customer_id": "C008", "status": "delivered", "total": 5997, "discount": 600, "shipping": 0, "final": 5397, "addr": "南京市雨花台区软件大道168号", "date": datetime(2026, 4, 12)},
            {"id": "O020", "order_no": "ORD-20260430-001", "customer_id": "C010", "status": "processing", "total": 2498, "discount": 250, "shipping": 0, "final": 2248, "addr": "重庆市渝北区新牌坊大道1号", "date": datetime(2026, 4, 30)},
        ]

        orders = []
        for o in orders_data:
            orders.append(Order(
                id=o["id"], order_no=o["order_no"], customer_id=o["customer_id"],
                status=o["status"], total_amount=Decimal(str(o["total"])),
                discount_amount=Decimal(str(o["discount"])), shipping_fee=Decimal(str(o["shipping"])),
                final_amount=Decimal(str(o["final"])), shipping_address=o["addr"],
                created_at=o["date"]
            ))
        session.add_all(orders)
        await session.commit()

        # ==================== 4. 创建订单商品 ====================
        order_items = [
            # O001: 智能手表Pro + 降噪耳机Pro + 表带套装
            OrderItem(order_id="O001", product_id="P001", product_name="智能手表Pro", quantity=1, unit_price=Decimal("1999.00"), subtotal=Decimal("1999.00")),
            OrderItem(order_id="O001", product_id="P006", product_name="降噪耳机Pro", quantity=1, unit_price=Decimal("1299.00"), subtotal=Decimal("1299.00")),
            OrderItem(order_id="O001", product_id="P001", product_name="智能手表Pro", quantity=1, unit_price=Decimal("1999.00"), subtotal=Decimal("1999.00")),
            # O002: 智能手表Pro
            OrderItem(order_id="O002", product_id="P001", product_name="智能手表Pro", quantity=1, unit_price=Decimal("1999.00"), subtotal=Decimal("1999.00")),
            # O003: 降噪耳机Pro
            OrderItem(order_id="O003", product_id="P006", product_name="降噪耳机Pro", quantity=1, unit_price=Decimal("1299.00"), subtotal=Decimal("1299.00")),
            # O004: 智能手表Pro + 降噪耳机Pro
            OrderItem(order_id="O004", product_id="P001", product_name="智能手表Pro", quantity=1, unit_price=Decimal("1999.00"), subtotal=Decimal("1999.00")),
            OrderItem(order_id="O004", product_id="P006", product_name="降噪耳机Pro", quantity=1, unit_price=Decimal("1299.00"), subtotal=Decimal("1299.00")),
            # O005: 智能手表Pro
            OrderItem(order_id="O005", product_id="P001", product_name="智能手表Pro", quantity=1, unit_price=Decimal("1999.00"), subtotal=Decimal("1999.00")),
            # O006: 降噪耳机Pro + 无线充电器
            OrderItem(order_id="O006", product_id="P006", product_name="降噪耳机Pro", quantity=1, unit_price=Decimal("1299.00"), subtotal=Decimal("1299.00")),
            OrderItem(order_id="O006", product_id="P009", product_name="无线充电器", quantity=1, unit_price=Decimal("149.00"), subtotal=Decimal("149.00")),
            # O007: 智能手环Pro + 表带套装
            OrderItem(order_id="O007", product_id="P004", product_name="智能手环Pro", quantity=1, unit_price=Decimal("499.00"), subtotal=Decimal("499.00")),
            OrderItem(order_id="O007", product_id="P011", product_name="表带套装", quantity=1, unit_price=Decimal("199.00"), subtotal=Decimal("199.00")),
            # O008: 智能手表Ultra
            OrderItem(order_id="O008", product_id="P003", product_name="智能手表Ultra", quantity=1, unit_price=Decimal("3999.00"), subtotal=Decimal("3999.00")),
            # O009: 降噪耳机Pro
            OrderItem(order_id="O009", product_id="P006", product_name="降噪耳机Pro", quantity=1, unit_price=Decimal("1299.00"), subtotal=Decimal("1299.00")),
            # O010: 智能手环Pro
            OrderItem(order_id="O010", product_id="P004", product_name="智能手环Pro", quantity=1, unit_price=Decimal("499.00"), subtotal=Decimal("499.00")),
            # O011: 智能手环Pro + 表带套装
            OrderItem(order_id="O011", product_id="P004", product_name="智能手环Pro", quantity=1, unit_price=Decimal("499.00"), subtotal=Decimal("499.00")),
            OrderItem(order_id="O011", product_id="P011", product_name="表带套装", quantity=1, unit_price=Decimal("199.00"), subtotal=Decimal("199.00")),
            # O012: 4个智能手表Pro
            OrderItem(order_id="O012", product_id="P001", product_name="智能手表Pro", quantity=4, unit_price=Decimal("1999.00"), subtotal=Decimal("7996.00")),
            # O013: 智能手表Pro + 智能手环Pro
            OrderItem(order_id="O013", product_id="P001", product_name="智能手表Pro", quantity=1, unit_price=Decimal("1999.00"), subtotal=Decimal("1999.00")),
            OrderItem(order_id="O013", product_id="P004", product_name="智能手环Pro", quantity=1, unit_price=Decimal("499.00"), subtotal=Decimal("499.00")),
            # O014: 降噪耳机Pro
            OrderItem(order_id="O014", product_id="P006", product_name="降噪耳机Pro", quantity=1, unit_price=Decimal("1299.00"), subtotal=Decimal("1299.00")),
            # O015: 智能手表Ultra
            OrderItem(order_id="O015", product_id="P003", product_name="智能手表Ultra", quantity=1, unit_price=Decimal("3999.00"), subtotal=Decimal("3999.00")),
            # O016: 无线耳机Lite (已取消)
            OrderItem(order_id="O016", product_id="P007", product_name="无线耳机Lite", quantity=1, unit_price=Decimal("399.00"), subtotal=Decimal("399.00")),
            # O017: 智能手环Lite
            OrderItem(order_id="O017", product_id="P005", product_name="智能手环Lite", quantity=1, unit_price=Decimal("199.00"), subtotal=Decimal("199.00")),
            # O018: 降噪耳机Pro
            OrderItem(order_id="O018", product_id="P006", product_name="降噪耳机Pro", quantity=1, unit_price=Decimal("1299.00"), subtotal=Decimal("1299.00")),
            # O019: 智能手表Pro x3
            OrderItem(order_id="O019", product_id="P001", product_name="智能手表Pro", quantity=3, unit_price=Decimal("1999.00"), subtotal=Decimal("5997.00")),
            # O020: 智能手表Pro + 智能手环Pro
            OrderItem(order_id="O020", product_id="P001", product_name="智能手表Pro", quantity=1, unit_price=Decimal("1999.00"), subtotal=Decimal("1999.00")),
            OrderItem(order_id="O020", product_id="P004", product_name="智能手环Pro", quantity=1, unit_price=Decimal("499.00"), subtotal=Decimal("499.00")),
        ]
        session.add_all(order_items)

        # ==================== 5. 创建发票 ====================
        invoices = [
            # C001 的发票
            Invoice(id="INV001", invoice_no="INV-20260115-001", customer_id="C001", order_id="O001", amount=Decimal("5397.00"), tax_amount=Decimal("701.61"), total_amount=Decimal("6098.61"), status="paid", paid_at=datetime(2026, 1, 15, 10, 30)),
            Invoice(id="INV002", invoice_no="INV-20260220-001", customer_id="C001", order_id="O002", amount=Decimal("1799.00"), tax_amount=Decimal("233.87"), total_amount=Decimal("2032.87"), status="paid", paid_at=datetime(2026, 2, 20, 14, 20)),
            Invoice(id="INV003", invoice_no="INV-20260310-001", customer_id="C001", order_id="O003", amount=Decimal("1299.00"), tax_amount=Decimal("168.87"), total_amount=Decimal("1467.87"), status="paid", paid_at=datetime(2026, 3, 10, 9, 15)),
            Invoice(id="INV004", invoice_no="INV-20260401-001", customer_id="C001", order_id="O004", amount=Decimal("2968.00"), tax_amount=Decimal("385.84"), total_amount=Decimal("3353.84"), status="paid", paid_at=datetime(2026, 4, 1, 11, 30)),
            Invoice(id="INV005", invoice_no="INV-20260425-001", customer_id="C001", order_id="O005", amount=Decimal("1999.00"), tax_amount=Decimal("259.87"), total_amount=Decimal("2258.87"), status="paid", paid_at=datetime(2026, 4, 25, 16, 45)),
            # C002 的发票
            Invoice(id="INV006", invoice_no="INV-20260205-001", customer_id="C002", order_id="O006", amount=Decimal("1424.00"), tax_amount=Decimal("185.12"), total_amount=Decimal("1609.12"), status="paid", paid_at=datetime(2026, 2, 5, 13, 20)),
            Invoice(id="INV007", invoice_no="INV-20260315-001", customer_id="C002", order_id="O007", amount=Decimal("608.00"), tax_amount=Decimal("79.04"), total_amount=Decimal("687.04"), status="paid", paid_at=datetime(2026, 3, 15, 10, 45)),
            Invoice(id="INV008", invoice_no="INV-20260410-001", customer_id="C002", order_id="O008", amount=Decimal("3599.00"), tax_amount=Decimal("467.87"), total_amount=Decimal("4066.87"), status="pending", due_date=datetime(2026, 5, 10)),
            Invoice(id="INV009", invoice_no="INV-20260428-001", customer_id="C002", order_id="O009", amount=Decimal("1299.00"), tax_amount=Decimal("168.87"), total_amount=Decimal("1467.87"), status="pending", due_date=datetime(2026, 5, 28)),
            # C003 的发票
            Invoice(id="INV010", invoice_no="INV-20260301-001", customer_id="C003", order_id="O010", amount=Decimal("509.00"), tax_amount=Decimal("66.17"), total_amount=Decimal("575.17"), status="paid", paid_at=datetime(2026, 3, 1, 15, 30)),
            Invoice(id="INV011", invoice_no="INV-20260405-001", customer_id="C003", order_id="O011", amount=Decimal("598.00"), tax_amount=Decimal("77.74"), total_amount=Decimal("675.74"), status="overdue", due_date=datetime(2026, 4, 20)),
            # C004 的发票
            Invoice(id="INV012", invoice_no="INV-20260120-001", customer_id="C004", order_id="O012", amount=Decimal("7196.00"), tax_amount=Decimal("935.48"), total_amount=Decimal("8131.48"), status="paid", paid_at=datetime(2026, 1, 20, 9, 0)),
            Invoice(id="INV013", invoice_no="INV-20260228-001", customer_id="C004", order_id="O013", amount=Decimal("2248.00"), tax_amount=Decimal("292.24"), total_amount=Decimal("2540.24"), status="paid", paid_at=datetime(2026, 2, 28, 14, 30)),
            Invoice(id="INV014", invoice_no="INV-20260320-001", customer_id="C004", order_id="O014", amount=Decimal("1299.00"), tax_amount=Decimal("168.87"), total_amount=Decimal("1467.87"), status="paid", paid_at=datetime(2026, 3, 20, 11, 15)),
            Invoice(id="INV015", invoice_no="INV-20260415-001", customer_id="C004", order_id="O015", amount=Decimal("3599.00"), tax_amount=Decimal("467.87"), total_amount=Decimal("4066.87"), status="paid", paid_at=datetime(2026, 4, 15, 10, 0)),
        ]
        session.add_all(invoices)

        # ==================== 6. 创建支付记录 ====================
        payments = [
            # C001 的支付
            Payment(id="PAY001", payment_no="PAY-20260115-001", order_id="O001", customer_id="C001", amount=Decimal("5397.00"), method="alipay", status="completed", transaction_id="ALI20260115001", created_at=datetime(2026, 1, 15, 10, 28)),
            Payment(id="PAY002", payment_no="PAY-20260220-001", order_id="O002", customer_id="C001", amount=Decimal("1799.00"), method="wechat", status="completed", transaction_id="WX20260220001", created_at=datetime(2026, 2, 20, 14, 18)),
            Payment(id="PAY003", payment_no="PAY-20260310-001", order_id="O003", customer_id="C001", amount=Decimal("1299.00"), method="alipay", status="completed", transaction_id="ALI20260310001", created_at=datetime(2026, 3, 10, 9, 12)),
            Payment(id="PAY004", payment_no="PAY-20260401-001", order_id="O004", customer_id="C001", amount=Decimal("2968.00"), method="credit_card", status="completed", transaction_id="CC20260401001", created_at=datetime(2026, 4, 1, 11, 28)),
            Payment(id="PAY005", payment_no="PAY-20260425-001", order_id="O005", customer_id="C001", amount=Decimal("1999.00"), method="wechat", status="completed", transaction_id="WX20260425001", created_at=datetime(2026, 4, 25, 16, 42)),
            # C002 的支付
            Payment(id="PAY006", payment_no="PAY-20260205-001", order_id="O006", customer_id="C002", amount=Decimal("1424.00"), method="alipay", status="completed", transaction_id="ALI20260205001", created_at=datetime(2026, 2, 5, 13, 18)),
            Payment(id="PAY007", payment_no="PAY-20260315-001", order_id="O007", customer_id="C002", amount=Decimal("608.00"), method="wechat", status="completed", transaction_id="WX20260315001", created_at=datetime(2026, 3, 15, 10, 42)),
            # C004 的支付
            Payment(id="PAY008", payment_no="PAY-20260120-001", order_id="O012", customer_id="C004", amount=Decimal("7196.00"), method="credit_card", status="completed", transaction_id="CC20260120001", created_at=datetime(2026, 1, 20, 8, 58)),
            Payment(id="PAY009", payment_no="PAY-20260228-001", order_id="O013", customer_id="C004", amount=Decimal("2248.00"), method="alipay", status="completed", transaction_id="ALI20260228001", created_at=datetime(2026, 2, 28, 14, 28)),
            Payment(id="PAY010", payment_no="PAY-20260320-001", order_id="O014", customer_id="C004", amount=Decimal("1299.00"), method="wechat", status="completed", transaction_id="WX20260320001", created_at=datetime(2026, 3, 20, 11, 12)),
            Payment(id="PAY011", payment_no="PAY-20260415-001", order_id="O015", customer_id="C004", amount=Decimal("3599.00"), method="credit_card", status="completed", transaction_id="CC20260415001", created_at=datetime(2026, 4, 15, 9, 58)),
            # C003 的支付
            Payment(id="PAY012", payment_no="PAY-20260301-001", order_id="O010", customer_id="C003", amount=Decimal("509.00"), method="alipay", status="completed", transaction_id="ALI20260301001", created_at=datetime(2026, 3, 1, 15, 28)),
        ]
        session.add_all(payments)

        # ==================== 7. 创建退款记录 ====================
        refunds = [
            Refund(id="R001", refund_no="REF-20260328-001", order_id="O016", customer_id="C005", amount=Decimal("399.00"), reason="不想要了，申请退款", status="approved", approved_by="agent1", approved_at=datetime(2026, 3, 28, 15, 30), created_at=datetime(2026, 3, 26, 10, 0)),
            Refund(id="R002", refund_no="REF-20260426-001", order_id="O005", customer_id="C001", amount=Decimal("1999.00"), reason="手表有质量问题，屏幕闪烁严重", status="pending", created_at=datetime(2026, 4, 26, 9, 30)),
            Refund(id="R003", refund_no="REF-20260420-001", order_id="O014", customer_id="C004", amount=Decimal("1299.00"), reason="耳机降噪效果不如预期", status="approved", approved_by="agent1", approved_at=datetime(2026, 4, 22, 14, 0), created_at=datetime(2026, 4, 20, 11, 0)),
            Refund(id="R004", refund_no="REF-20260410-001", order_id="O010", customer_id="C003", amount=Decimal("499.00"), reason="手环心率监测不准确", status="rejected", rejection_reason="经检测心率监测功能正常", created_at=datetime(2026, 4, 10, 16, 0)),
        ]
        session.add_all(refunds)

        # ==================== 8. 创建物流记录 ====================
        shipments = [
            Shipment(id="S001", shipment_no="SF20260401001", order_id="O004", carrier="顺丰速运", tracking_no="SF1234567890", status="delivered", shipped_at=datetime(2026, 4, 2, 10, 0), delivered_at=datetime(2026, 4, 4, 14, 30), estimated_delivery=datetime(2026, 4, 5), current_location="已签收"),
            Shipment(id="S002", shipment_no="SF20260410001", order_id="O008", carrier="顺丰速运", tracking_no="SF9876543210", status="in_transit", shipped_at=datetime(2026, 4, 11, 9, 0), estimated_delivery=datetime(2026, 4, 13), current_location="上海转运中心"),
            Shipment(id="S003", shipment_no="YT20260425001", order_id="O005", carrier="圆通速递", tracking_no="YT1234567890", status="delivered", shipped_at=datetime(2026, 4, 26, 11, 0), delivered_at=datetime(2026, 4, 28, 10, 15), estimated_delivery=datetime(2026, 4, 29), current_location="已签收"),
            Shipment(id="S004", shipment_no="ZT20260428001", order_id="O009", carrier="中通快递", tracking_no="ZT1234567890", status="shipped", shipped_at=datetime(2026, 4, 29, 14, 0), estimated_delivery=datetime(2026, 5, 2), current_location="上海集散中心"),
            Shipment(id="S005", shipment_no="SF20260430001", order_id="O020", carrier="顺丰速运", tracking_no="SF1122334455", status="pending", estimated_delivery=datetime(2026, 5, 3), current_location="等待揽收"),
        ]
        session.add_all(shipments)

        # 物流追踪事件
        tracking_events = [
            # S001 的追踪
            ShipmentTracking(shipment_id="S001", event_type="picked_up", location="深圳仓库", description="包裹已揽收", event_time=datetime(2026, 4, 2, 10, 0)),
            ShipmentTracking(shipment_id="S001", event_type="in_transit", location="深圳转运中心", description="包裹已到达深圳转运中心", event_time=datetime(2026, 4, 2, 18, 0)),
            ShipmentTracking(shipment_id="S001", event_type="in_transit", location="北京转运中心", description="包裹已到达北京转运中心", event_time=datetime(2026, 4, 3, 22, 0)),
            ShipmentTracking(shipment_id="S001", event_type="out_for_delivery", location="北京朝阳区", description="快递员正在派送", event_time=datetime(2026, 4, 4, 9, 0)),
            ShipmentTracking(shipment_id="S001", event_type="delivered", location="北京市朝阳区建国路88号", description="包裹已签收，签收人：本人", event_time=datetime(2026, 4, 4, 14, 30)),
            # S002 的追踪
            ShipmentTracking(shipment_id="S002", event_type="picked_up", location="深圳仓库", description="包裹已揽收", event_time=datetime(2026, 4, 11, 9, 0)),
            ShipmentTracking(shipment_id="S002", event_type="in_transit", location="深圳转运中心", description="包裹已到达深圳转运中心", event_time=datetime(2026, 4, 11, 20, 0)),
            ShipmentTracking(shipment_id="S002", event_type="in_transit", location="上海转运中心", description="包裹已到达上海转运中心", event_time=datetime(2026, 4, 12, 15, 0)),
            # S003 的追踪
            ShipmentTracking(shipment_id="S003", event_type="picked_up", location="深圳仓库", description="包裹已揽收", event_time=datetime(2026, 4, 26, 11, 0)),
            ShipmentTracking(shipment_id="S003", event_type="in_transit", location="杭州转运中心", description="包裹已到达杭州转运中心", event_time=datetime(2026, 4, 27, 3, 0)),
            ShipmentTracking(shipment_id="S003", event_type="out_for_delivery", location="杭州西湖区", description="快递员正在派送", event_time=datetime(2026, 4, 28, 8, 0)),
            ShipmentTracking(shipment_id="S003", event_type="delivered", location="杭州市西湖区文三路90号", description="包裹已签收，签收人：前台代收", event_time=datetime(2026, 4, 28, 10, 15)),
        ]
        session.add_all(tracking_events)

        # ==================== 9. 创建订单状态历史 ====================
        status_history = [
            # O001
            OrderStatusHistory(order_id="O001", old_status=None, new_status="pending", changed_by="system", notes="订单创建", created_at=datetime(2026, 1, 15, 10, 0)),
            OrderStatusHistory(order_id="O001", old_status="pending", new_status="processing", changed_by="system", notes="支付成功", created_at=datetime(2026, 1, 15, 10, 28)),
            OrderStatusHistory(order_id="O001", old_status="processing", new_status="shipped", changed_by="system", notes="包裹已发出", created_at=datetime(2026, 1, 16, 9, 0)),
            OrderStatusHistory(order_id="O001", old_status="shipped", new_status="delivered", changed_by="system", notes="包裹已签收", created_at=datetime(2026, 1, 18, 14, 0)),
            # O005
            OrderStatusHistory(order_id="O005", old_status=None, new_status="pending", changed_by="system", notes="订单创建", created_at=datetime(2026, 4, 25, 16, 40)),
            OrderStatusHistory(order_id="O005", old_status="pending", new_status="processing", changed_by="system", notes="支付成功", created_at=datetime(2026, 4, 25, 16, 42)),
            OrderStatusHistory(order_id="O005", old_status="processing", new_status="shipped", changed_by="system", notes="包裹已发出，快递单号：YT1234567890", created_at=datetime(2026, 4, 26, 11, 0)),
            OrderStatusHistory(order_id="O005", old_status="shipped", new_status="delivered", changed_by="system", notes="包裹已签收", created_at=datetime(2026, 4, 28, 10, 15)),
            # O016 (已取消)
            OrderStatusHistory(order_id="O016", old_status=None, new_status="pending", changed_by="system", notes="订单创建", created_at=datetime(2026, 3, 25, 10, 0)),
            OrderStatusHistory(order_id="O016", old_status="pending", new_status="cancelled", changed_by="customer", notes="客户主动取消", created_at=datetime(2026, 3, 26, 9, 0)),
        ]
        session.add_all(status_history)

        # ==================== 10. 创建工单 ====================
        tickets = [
            SupportTicket(id="T001", ticket_no="TK-20260120-001", customer_id="C001", order_id="O001", category="technical", title="智能手表Pro无法开机", description="手表充电一晚后仍然无法开机，长按电源键也没反应", priority="high", status="resolved", assigned_to="agent1", resolution="长按电源键15秒强制重启，已恢复正常", resolved_at=datetime(2026, 1, 21, 10, 0)),
            SupportTicket(id="T002", ticket_no="TK-20260305-001", customer_id="C002", order_id="O006", category="technical", title="降噪耳机连接不稳定", description="耳机与手机连接后经常断开，特别是在地铁上", priority="medium", status="open", assigned_to="agent1"),
            SupportTicket(id="T003", ticket_no="TK-20260318-001", customer_id="C003", category="billing", title="账单金额有疑问", description="订单ORD-20260405-001的账单金额与商品价格不符，多了10元", priority="medium", status="open"),
            SupportTicket(id="T004", ticket_no="TK-20260422-001", customer_id="C004", order_id="O014", category="refund", title="退款进度查询", description="申请退款已经5天了，还没有收到退款，麻烦帮忙查一下", priority="high", status="open", assigned_to="agent1"),
            SupportTicket(id="T005", ticket_no="TK-20260425-001", customer_id="C001", order_id="O005", category="technical", title="手表屏幕闪烁", description="智能手表Pro屏幕经常闪烁，特别是在低亮度下更明显", priority="high", status="open"),
            SupportTicket(id="T006", ticket_no="TK-20260428-001", customer_id="C006", order_id="O018", category="delivery", title="物流信息三天没更新", description="包裹显示在上海转运中心已经3天了，一直没有更新物流信息", priority="medium", status="open"),
            SupportTicket(id="T007", ticket_no="TK-20260429-001", customer_id="C008", category="complaint", title="客服态度问题", description="之前咨询问题时，客服回复很慢而且答非所问，体验很差", priority="high", status="in_progress", assigned_to="supervisor"),
            SupportTicket(id="T008", ticket_no="TK-20260430-001", customer_id="C010", order_id="O020", category="exchange", title="换货申请", description="收到的智能手表Pro有划痕，想要换货", priority="medium", status="open"),
        ]
        session.add_all(tickets)

        # ==================== 11. 创建知识库文章 ====================
        articles = [
            KnowledgeArticle(title="智能手表Pro无法开机怎么办", content="如果您的智能手表Pro无法开机，请按以下步骤排查：\n\n1. **检查充电**：确保充电器正常工作，尝试更换充电线\n2. **强制重启**：长按电源键10秒进行强制重启\n3. **检查电池**：如果电池完全耗尽，需要充电30分钟后再尝试开机\n4. **恢复出厂设置**：同时按住电源键和功能键5秒\n\n如果以上方法都无法解决，可能是硬件故障，建议联系售后进行维修。", category="technical", tags='["手表","开机","故障","维修"]', view_count=1256),
            KnowledgeArticle(title="如何连接蓝牙耳机", content="连接蓝牙耳机的步骤：\n\n1. 打开耳机充电盒，耳机自动进入配对模式（指示灯闪烁）\n2. 打开手机蓝牙设置\n3. 在设备列表中找到您的耳机名称（如 AudioMax-Pro）\n4. 点击连接，等待配对完成\n5. 连接成功后会提示音\n\n**常见问题**：\n- 如果搜不到耳机，请确保耳机在配对模式\n- 如果连接失败，请删除配对记录后重试\n- 地铁等干扰大的环境可能会断连，这是正常现象", category="technical", tags='["耳机","蓝牙","连接","配对"]', view_count=2345),
            KnowledgeArticle(title="退款政策说明", content="我们的退款政策如下：\n\n**退款条件**\n- 未拆封商品：7天内无理由退款\n- 已拆封商品：15天内因质量问题可退款\n- 定制商品：不支持退款\n\n**退款流程**\n1. 提交退款申请\n2. 客服审核（1-3个工作日）\n3. 审核通过后，3-5个工作日到账\n\n**退款方式**\n- 原路退回（支付宝/微信/银行卡）\n- 退到账户余额（即时到账）\n\n**特殊情况**\n- 大额退款（>2000元）需要财务审批\n- 已开发票的订单需要先退回发票", category="refund", tags='["退款","政策","流程"]', view_count=3456),
            KnowledgeArticle(title="会员等级说明", content="会员等级及权益：\n\n| 等级 | 条件 | 权益 |\n|------|------|------|\n| 普通会员 | 注册即得 | 基础服务 |\n| 银卡会员 | 累计消费≥5000元 | 95折优惠、优先客服、生日礼包 |\n| 金卡会员 | 累计消费≥20000元 | 9折优惠、专属客服、免费退换货、优先发货 |\n\n**积分规则**\n- 消费1元=1积分\n- 100积分=1元（可抵扣）\n- 积分有效期：12个月\n\n**升降级规则**\n- 每季度评估一次\n- 降级保护：连续2个季度不达标才降级", category="general", tags='["会员","等级","权益","积分"]', view_count=4567),
            KnowledgeArticle(title="保修服务说明", content="保修政策：\n\n**保修期限**\n- 手表类：24个月保修\n- 耳机类：12个月保修\n- 配件类：6个月保修\n\n**保修范围**\n- 非人为损坏的质量问题\n- 正常使用出现的故障\n- 软件系统问题\n\n**不在保修范围**\n- 进水、摔坏、私自拆修\n- 超过保修期\n- 非官方渠道购买\n\n**保修流程**\n1. 联系客服，描述问题\n2. 提供购买凭证（订单号）\n3. 客服判断是否在保修范围\n4. 寄回产品进行检测\n5. 检测通过后免费维修或更换", category="technical", tags='["保修","售后","维修"]', view_count=1890),
            KnowledgeArticle(title="常见支付问题解答", content="**支付失败怎么办？**\n\n1. 检查银行卡余额是否充足\n2. 检查银行卡是否开通网上支付\n3. 检查支付密码是否正确\n4. 尝试更换支付方式\n\n**支持的支付方式**\n- 支付宝\n- 微信支付\n- 银行卡（借记卡/信用卡）\n- 花呗分期\n\n**支付安全**\n- 所有支付信息加密传输\n- 不会存储您的银行卡密码\n- 大额支付需要短信验证", category="billing", tags='["支付","安全","银行卡"]', view_count=2100),
            KnowledgeArticle(title="物流查询与催单", content="**如何查询物流？**\n\n1. 登录账户，进入订单详情\n2. 查看物流信息和追踪记录\n3. 也可以复制快递单号到快递公司官网查询\n\n**物流状态说明**\n- 待揽收：商家已打包，等待快递员取件\n- 已揽收：快递员已取件\n- 运输中：包裹在转运途中\n- 派送中：快递员正在派送\n- 已签收：包裹已送达\n\n**催单处理**\n- 如果物流超过3天没更新，可以联系客服催单\n- 如果显示已签收但未收到，请联系客服核实", category="delivery", tags='["物流","查询","催单"]', view_count=3200),
            KnowledgeArticle(title="产品使用技巧 - 智能手表", content="**智能手表Pro使用技巧**\n\n1. **快速唤醒**：抬腕即可亮屏\n2. **快捷支付**：双击侧键打开付款码\n3. **运动模式**：长按功能键选择运动类型\n4. **表盘更换**：长按表盘进入选择界面\n5. **省电模式**：下拉菜单开启省电模式\n\n**日常保养**\n- 避免长时间浸泡在水中\n- 定期清洁表带\n- 避免在极端温度下使用\n- 定期更新固件\n\n**常见问题**\n- 心率监测不准：确保手表佩戴紧贴皮肤\n- GPS定位慢：首次定位需要1-2分钟\n- 通知不接收：检查手机APP权限设置", category="technical", tags='["手表","使用","技巧","保养"]', view_count=5678),
        ]
        session.add_all(articles)

        # ==================== 12. 创建优惠券 ====================
        coupons = [
            Coupon(id="CPN001", code="NEWUSER50", name="新用户50元券", description="新用户专享，满200减50", discount_type="fixed", discount_value=Decimal("50.00"), min_order_amount=Decimal("200.00"), usage_limit=1, used_count=0, valid_from=datetime(2026, 1, 1), valid_until=datetime(2026, 12, 31), is_active=True),
            Coupon(id="CPN002", code="VIP10OFF", name="VIP会员9折券", description="全场9折优惠，最高减500元", discount_type="percentage", discount_value=Decimal("10.00"), min_order_amount=Decimal("100.00"), max_discount=Decimal("500.00"), usage_limit=1, used_count=0, valid_from=datetime(2026, 4, 1), valid_until=datetime(2026, 6, 30), is_active=True),
            Coupon(id="CPN003", code="WATCH100", name="手表专区100元券", description="手表类商品满1000减100", discount_type="fixed", discount_value=Decimal("100.00"), min_order_amount=Decimal("1000.00"), usage_limit=1, used_count=0, valid_from=datetime(2026, 4, 1), valid_until=datetime(2026, 5, 31), is_active=True),
            Coupon(id="CPN004", code="SPRING20", name="春季大促8折券", description="全场8折优惠，最高减1000元", discount_type="percentage", discount_value=Decimal("20.00"), min_order_amount=Decimal("500.00"), max_discount=Decimal("1000.00"), usage_limit=1, used_count=0, valid_from=datetime(2026, 3, 1), valid_until=datetime(2026, 3, 31), is_active=False),
            Coupon(id="CPN005", code="FREESHIP", name="免运费券", description="全场免运费", discount_type="fixed", discount_value=Decimal("10.00"), min_order_amount=Decimal("0.00"), usage_limit=3, used_count=0, valid_from=datetime(2026, 4, 1), valid_until=datetime(2026, 6, 30), is_active=True),
        ]
        session.add_all(coupons)

        # ==================== 13. 创建客户优惠券关联 ====================
        customer_coupons = [
            CustomerCoupon(customer_id="C001", coupon_id="CPN001", is_used=True, used_at=datetime(2026, 1, 15), order_id="O001"),
            CustomerCoupon(customer_id="C001", coupon_id="CPN002", is_used=False),
            CustomerCoupon(customer_id="C001", coupon_id="CPN003", is_used=False),
            CustomerCoupon(customer_id="C002", coupon_id="CPN001", is_used=True, used_at=datetime(2026, 2, 5), order_id="O006"),
            CustomerCoupon(customer_id="C002", coupon_id="CPN005", is_used=False),
            CustomerCoupon(customer_id="C003", coupon_id="CPN001", is_used=False),
            CustomerCoupon(customer_id="C004", coupon_id="CPN001", is_used=True, used_at=datetime(2026, 1, 20), order_id="O012"),
            CustomerCoupon(customer_id="C004", coupon_id="CPN002", is_used=False),
            CustomerCoupon(customer_id="C004", coupon_id="CPN003", is_used=True, used_at=datetime(2026, 4, 15), order_id="O015"),
        ]
        session.add_all(customer_coupons)

        # ==================== 14. 创建积分记录 ====================
        loyalty_points = [
            LoyaltyPoints(customer_id="C001", points=5397, balance=5397, type="earned", description="订单ORD-20260115-001消费获得", reference_id="ORD-20260115-001", created_at=datetime(2026, 1, 15)),
            LoyaltyPoints(customer_id="C001", points=1799, balance=7196, type="earned", description="订单ORD-20260220-001消费获得", reference_id="ORD-20260220-001", created_at=datetime(2026, 2, 20)),
            LoyaltyPoints(customer_id="C001", points=-1400, balance=5796, type="redeemed", description="积分兑换优惠券", reference_id="CPN002", created_at=datetime(2026, 3, 1)),
            LoyaltyPoints(customer_id="C001", points=2968, balance=8764, type="earned", description="订单ORD-20260401-001消费获得", reference_id="ORD-20260401-001", created_at=datetime(2026, 4, 1)),
            LoyaltyPoints(customer_id="C001", points=-2964, balance=5800, type="redeemed", description="积分抵扣订单ORD-20260401-001部分金额", reference_id="ORD-20260401-001", created_at=datetime(2026, 4, 1)),
            LoyaltyPoints(customer_id="C002", points=1424, balance=1424, type="earned", description="订单ORD-20260205-001消费获得", reference_id="ORD-20260205-001", created_at=datetime(2026, 2, 5)),
            LoyaltyPoints(customer_id="C002", points=608, balance=2032, type="earned", description="订单ORD-20260315-001消费获得", reference_id="ORD-20260315-001", created_at=datetime(2026, 3, 15)),
            LoyaltyPoints(customer_id="C002", points=1168, balance=3200, type="earned", description="订单ORD-20260410-001消费获得", reference_id="ORD-20260410-001", created_at=datetime(2026, 4, 10)),
            LoyaltyPoints(customer_id="C004", points=7196, balance=7196, type="earned", description="订单ORD-20260120-001消费获得", reference_id="ORD-20260120-001", created_at=datetime(2026, 1, 20)),
            LoyaltyPoints(customer_id="C004", points=2248, balance=9444, type="earned", description="订单ORD-20260228-001消费获得", reference_id="ORD-20260228-001", created_at=datetime(2026, 2, 28)),
            LoyaltyPoints(customer_id="C004", points=-544, balance=8900, type="redeemed", description="积分兑换运费", reference_id="O014", created_at=datetime(2026, 3, 20)),
        ]
        session.add_all(loyalty_points)

        # ==================== 15. 创建产品评价 ====================
        reviews = [
            ProductReview(product_id="P001", customer_id="C001", order_id="O001", rating=5, title="非常好用的手表", content="功能齐全，续航给力，心率监测很准确，推荐购买！"),
            ProductReview(product_id="P001", customer_id="C002", order_id="O006", rating=4, title="整体不错", content="手表很好用，但是表带材质一般，希望可以改进"),
            ProductReview(product_id="P001", customer_id="C004", order_id="O012", rating=5, title="买了4个送家人", content="全家人都很喜欢，功能强大，性价比高"),
            ProductReview(product_id="P006", customer_id="C001", order_id="O001", rating=4, title="降噪效果好", content="降噪效果很好，音质也不错，就是戴久了耳朵有点疼"),
            ProductReview(product_id="P006", customer_id="C004", order_id="O014", rating=3, title="降噪不如预期", content="降噪效果没有宣传的那么好，在嘈杂环境下还是能听到噪音"),
            ProductReview(product_id="P004", customer_id="C003", order_id="O010", rating=5, title="运动必备", content="防水效果好，运动时佩戴很方便，数据记录准确"),
            ProductReview(product_id="P003", customer_id="C002", order_id="O008", rating=5, title="专业运动手表", content="钛合金表壳质感很好，100米防水真的可以游泳佩戴"),
            ProductReview(product_id="P005", customer_id="C005", order_id="O017", rating=4, title="性价比高", content="价格便宜功能够用，就是续航一般，需要经常充电"),
            ProductReview(product_id="P009", customer_id="C002", order_id="O006", rating=4, title="充电方便", content="无线充电很方便，就是充电速度有线快充慢一些"),
            ProductReview(product_id="P014", customer_id="C006", order_id="O018", rating=5, title="数据准确", content="体脂秤数据很准确，APP同步也很方便，推荐健身人士使用"),
        ]
        session.add_all(reviews)

        # ==================== 16. 创建客户反馈 ====================
        feedback = [
            CustomerFeedback(customer_id="C001", order_id="O001", type="praise", category="产品质量", subject="智能手表Pro质量很好", content="用了3个月了，没有任何问题，功能强大，值得推荐", rating=5, status="resolved", response="感谢您的好评！我们会继续努力提供优质产品", responded_by="system", responded_at=datetime(2026, 4, 15)),
            CustomerFeedback(customer_id="C002", type="complaint", category="物流服务", subject="物流太慢了", content="从深圳到上海居然用了5天，比其他快递公司慢太多了", rating=2, status="in_review"),
            CustomerFeedback(customer_id="C003", type="suggestion", category="产品功能", subject="希望手表支持更多表盘", content="现在的表盘样式太少了，希望可以开放自定义表盘功能", rating=None, status="pending"),
            CustomerFeedback(customer_id="C004", order_id="O014", type="complaint", category="产品质量", subject="降噪效果不如宣传", content="降噪耳机Pro的降噪效果没有广告说的那么好，和竞品差距明显", rating=3, status="in_review"),
            CustomerFeedback(customer_id="C006", type="question", category="售后服务", subject="保修期怎么计算", content="我在第三方平台买的，保修期是从购买日开始算还是从出厂日算？", rating=None, status="pending"),
            CustomerFeedback(customer_id="C008", type="complaint", category="客服服务", subject="客服响应太慢", content="咨询问题等了30分钟才有人回复，而且回答很敷衍", rating=1, status="in_progress", responded_by="supervisor"),
            CustomerFeedback(customer_id="C010", order_id="O020", type="complaint", category="产品质量", subject="收到的产品有划痕", content="刚收到的手表Pro表壳有明显划痕，怀疑是二手的", rating=1, status="pending"),
        ]
        session.add_all(feedback)

        # 提交所有数据
        await session.commit()

        print("=" * 60)
        print("[OK] 测试数据填充完成！")
        print("=" * 60)
        print(f"  - 商品: {len(products)} 个")
        print(f"  - 客户: {len(customers)} 个")
        print(f"  - 订单: {len(orders)} 个")
        print(f"  - 订单商品: {len(order_items)} 个")
        print(f"  - 发票: {len(invoices)} 条")
        print(f"  - 支付记录: {len(payments)} 条")
        print(f"  - 退款记录: {len(refunds)} 条")
        print(f"  - 物流记录: {len(shipments)} 条")
        print(f"  - 物流追踪: {len(tracking_events)} 条")
        print(f"  - 状态历史: {len(status_history)} 条")
        print(f"  - 工单: {len(tickets)} 条")
        print(f"  - 知识库: {len(articles)} 篇")
        print(f"  - 优惠券: {len(coupons)} 张")
        print(f"  - 客户优惠券: {len(customer_coupons)} 条")
        print(f"  - 积分记录: {len(loyalty_points)} 条")
        print(f"  - 产品评价: {len(reviews)} 条")
        print(f"  - 客户反馈: {len(feedback)} 条")


if __name__ == "__main__":
    asyncio.run(seed_database())
