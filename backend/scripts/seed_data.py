from __future__ import annotations

import asyncio
import json
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
    Invoice,
    KnowledgeArticle,
    Order,
    OrderItem,
    Payment,
    Product,
    Refund,
    SupportTicket,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def seed_database():
    """填充测试数据"""
    engine = get_engine()

    # 先创建表
    await init_db()

    async with AsyncSession(engine) as session:
        # 清空现有数据
        for table in ["support_tickets", "knowledge_articles", "refunds", "payments", "invoices", "order_items", "orders", "products", "customers"]:
            await session.execute(text(f"DELETE FROM {table}"))
        await session.commit()

        # 1. 创建商品
        products = [
            Product(id="P001", sku="WATCH-PRO-001", name="智能手表Pro", description="高端智能手表，支持心率监测、GPS定位、NFC支付、血氧检测", category="手表", price=Decimal("1999.00"), stock=100, warranty_months=24),
            Product(id="P002", sku="WATCH-LITE-001", name="智能手表Lite", description="轻量级智能手表，支持运动追踪、消息通知、睡眠监测", category="手表", price=Decimal("999.00"), stock=200, warranty_months=12),
            Product(id="P003", sku="BAND-PRO-001", name="智能手环Pro", description="专业运动手环，支持心率、血氧、压力监测，50米防水", category="手环", price=Decimal("499.00"), stock=300, warranty_months=12),
            Product(id="P004", sku="BAND-LITE-001", name="智能手环Lite", description="入门级运动手环，支持步数统计、睡眠监测、消息提醒", category="手环", price=Decimal("199.00"), stock=500, warranty_months=6),
            Product(id="P005", sku="EARBUDS-PRO-001", name="降噪耳机Pro", description="主动降噪无线耳机，支持空间音频、多点连接", category="耳机", price=Decimal("1299.00"), stock=150, warranty_months=12),
            Product(id="P006", sku="EARBUDS-LITE-001", name="无线耳机Lite", description="轻便无线耳机，支持蓝牙5.0，续航8小时", category="耳机", price=Decimal("399.00"), stock=400, warranty_months=6),
            Product(id="P007", sku="CHARGER-001", name="无线充电器", description="15W无线快充，支持Qi协议，兼容多设备", category="配件", price=Decimal("149.00"), stock=1000, warranty_months=6),
            Product(id="P008", sku="STRAP-001", name="表带套装", description="3条不同风格表带，适配智能手表Pro/Lite", category="配件", price=Decimal("99.00"), stock=800, warranty_months=3),
        ]
        session.add_all(products)

        # 2. 创建客户
        customers = [
            Customer(id="C001", name="张三", email="zhangsan@example.com", phone="13800138001", address="北京市朝阳区建国路88号", vip_level="gold"),
            Customer(id="C002", name="李四", email="lisi@example.com", phone="13800138002", address="上海市浦东新区陆家嘴100号", vip_level="silver"),
            Customer(id="C003", name="王五", email="wangwu@example.com", phone="13800138003", address="广州市天河区天河路385号", vip_level="normal"),
            Customer(id="C004", name="赵六", email="zhaoliu@example.com", phone="13800138004", address="深圳市南山区科技园路1号", vip_level="gold"),
            Customer(id="C005", name="钱七", email="qianqi@example.com", phone="13800138005", address="杭州市西湖区文三路90号", vip_level="normal"),
        ]
        session.add_all(customers)

        # 3. 创建订单
        orders = [
            Order(id="O001", order_no="ORD-20260401-001", customer_id="C001", status="delivered", total_amount=Decimal("3298.00"), shipping_address="北京市朝阳区建国路88号"),
            Order(id="O002", order_no="ORD-20260402-001", customer_id="C001", status="delivered", total_amount=Decimal("1999.00"), shipping_address="北京市朝阳区建国路88号"),
            Order(id="O003", order_no="ORD-20260405-001", customer_id="C002", status="shipped", total_amount=Decimal("1499.00"), shipping_address="上海市浦东新区陆家嘴100号"),
            Order(id="O004", order_no="ORD-20260410-001", customer_id="C003", status="pending", total_amount=Decimal("598.00"), shipping_address="广州市天河区天河路385号"),
            Order(id="O005", order_no="ORD-20260415-001", customer_id="C004", status="delivered", total_amount=Decimal("2498.00"), shipping_address="深圳市南山区科技园路1号"),
            Order(id="O006", order_no="ORD-20260420-001", customer_id="C005", status="cancelled", total_amount=Decimal("399.00"), shipping_address="杭州市西湖区文三路90号"),
            Order(id="O007", order_no="ORD-20260425-001", customer_id="C002", status="processing", total_amount=Decimal("1299.00"), shipping_address="上海市浦东新区陆家嘴100号"),
        ]
        session.add_all(orders)

        # 4. 创建订单商品
        order_items = [
            OrderItem(order_id="O001", product_id="P001", product_name="智能手表Pro", quantity=1, unit_price=Decimal("1999.00"), subtotal=Decimal("1999.00")),
            OrderItem(order_id="O001", product_id="P005", product_name="降噪耳机Pro", quantity=1, unit_price=Decimal("1299.00"), subtotal=Decimal("1299.00")),
            OrderItem(order_id="O002", product_id="P001", product_name="智能手表Pro", quantity=1, unit_price=Decimal("1999.00"), subtotal=Decimal("1999.00")),
            OrderItem(order_id="O003", product_id="P005", product_name="降噪耳机Pro", quantity=1, unit_price=Decimal("1299.00"), subtotal=Decimal("1299.00")),
            OrderItem(order_id="O003", product_id="P007", product_name="无线充电器", quantity=1, unit_price=Decimal("149.00"), subtotal=Decimal("149.00")),
            OrderItem(order_id="O004", product_id="P003", product_name="智能手环Pro", quantity=1, unit_price=Decimal("499.00"), subtotal=Decimal("499.00")),
            OrderItem(order_id="O004", product_id="P008", product_name="表带套装", quantity=1, unit_price=Decimal("99.00"), subtotal=Decimal("99.00")),
            OrderItem(order_id="O005", product_id="P001", product_name="智能手表Pro", quantity=1, unit_price=Decimal("1999.00"), subtotal=Decimal("1999.00")),
            OrderItem(order_id="O005", product_id="P003", product_name="智能手环Pro", quantity=1, unit_price=Decimal("499.00"), subtotal=Decimal("499.00")),
            OrderItem(order_id="O006", product_id="P006", product_name="无线耳机Lite", quantity=1, unit_price=Decimal("399.00"), subtotal=Decimal("399.00")),
            OrderItem(order_id="O007", product_id="P005", product_name="降噪耳机Pro", quantity=1, unit_price=Decimal("1299.00"), subtotal=Decimal("1299.00")),
        ]
        session.add_all(order_items)

        # 5. 创建发票
        invoices = [
            Invoice(id="INV001", invoice_no="INV-20260401-001", customer_id="C001", order_id="O001", amount=Decimal("3298.00"), status="paid", paid_at=datetime(2026, 4, 1, 10, 30)),
            Invoice(id="INV002", invoice_no="INV-20260402-001", customer_id="C001", order_id="O002", amount=Decimal("1999.00"), status="paid", paid_at=datetime(2026, 4, 2, 14, 20)),
            Invoice(id="INV003", invoice_no="INV-20260405-001", customer_id="C002", order_id="O003", amount=Decimal("1499.00"), status="pending", due_date=datetime(2026, 5, 5)),
            Invoice(id="INV004", invoice_no="INV-20260410-001", customer_id="C003", order_id="O004", amount=Decimal("598.00"), status="pending", due_date=datetime(2026, 5, 10)),
            Invoice(id="INV005", invoice_no="INV-20260415-001", customer_id="C004", order_id="O005", amount=Decimal("2498.00"), status="paid", paid_at=datetime(2026, 4, 15, 9, 15)),
        ]
        session.add_all(invoices)

        # 6. 创建支付记录
        payments = [
            Payment(id="PAY001", payment_no="PAY-20260401-001", order_id="O001", customer_id="C001", amount=Decimal("3298.00"), method="alipay", status="completed", transaction_id="ALI20260401001"),
            Payment(id="PAY002", payment_no="PAY-20260402-001", order_id="O002", customer_id="C001", amount=Decimal("1999.00"), method="wechat", status="completed", transaction_id="WX20260402001"),
            Payment(id="PAY003", payment_no="PAY-20260415-001", order_id="O005", customer_id="C004", amount=Decimal("2498.00"), method="credit_card", status="completed", transaction_id="CC20260415001"),
        ]
        session.add_all(payments)

        # 7. 创建退款记录
        refunds = [
            Refund(id="R001", refund_no="REF-20260420-001", order_id="O006", customer_id="C005", amount=Decimal("399.00"), reason="不想要了，申请退款", status="approved", approved_by="system", approved_at=datetime(2026, 4, 20, 15, 30)),
            Refund(id="R002", refund_no="REF-20260425-001", order_id="O002", customer_id="C001", amount=Decimal("1999.00"), reason="手表有质量问题，屏幕闪烁", status="pending"),
        ]
        session.add_all(refunds)

        # 8. 创建工单
        tickets = [
            SupportTicket(id="T001", ticket_no="TK-20260401-001", customer_id="C001", order_id="O001", category="technical", title="智能手表Pro无法开机", description="手表充电一晚后仍然无法开机，长按电源键也没反应", priority="high", status="resolved"),
            SupportTicket(id="T002", ticket_no="TK-20260410-001", customer_id="C002", order_id="O003", category="technical", title="降噪耳机连接不稳定", description="耳机与手机连接后经常断开，特别是在地铁上", priority="medium", status="open"),
            SupportTicket(id="T003", ticket_no="TK-20260415-001", customer_id="C003", category="billing", title="账单金额有疑问", description="订单ORD-20260410-001的账单金额与商品价格不符", priority="medium", status="open"),
            SupportTicket(id="T004", ticket_no="TK-20260420-001", customer_id="C004", order_id="O005", category="refund", title="退款进度查询", description="申请退款已经5天了，还没有收到退款", priority="high", status="open"),
        ]
        session.add_all(tickets)

        # 9. 创建知识库文章
        articles = [
            KnowledgeArticle(title="智能手表Pro无法开机怎么办", content="如果您的智能手表Pro无法开机，请按以下步骤排查：\n1. 检查充电器是否正常工作，尝试更换充电线\n2. 长按电源键10秒进行强制重启\n3. 如果仍然无法开机，可能是电池损坏，建议联系售后", category="technical", tags='["手表","开机","故障"]'),
            KnowledgeArticle(title="如何连接蓝牙耳机", content="连接蓝牙耳机的步骤：\n1. 打开耳机充电盒，耳机自动进入配对模式\n2. 打开手机蓝牙设置\n3. 在设备列表中找到您的耳机名称\n4. 点击连接，等待配对完成", category="technical", tags='["耳机","蓝牙","连接"]'),
            KnowledgeArticle(title="退款政策说明", content="我们的退款政策如下：\n1. 未拆封商品：7天内无理由退款\n2. 已拆封商品：15天内因质量问题可退款\n3. 退款审核时间：1-3个工作日\n4. 退款到账时间：审核通过后3-5个工作日", category="refund", tags='["退款","政策"]'),
            KnowledgeArticle(title="会员等级说明", content="会员等级及权益：\n- 普通会员：基础服务\n- 银卡会员：95折优惠，优先客服\n- 金卡会员：9折优惠，专属客服，免费退换货\n- 升级条件：累计消费满5000元升银卡，满20000元升金卡", category="general", tags='["会员","等级","权益"]'),
            KnowledgeArticle(title="保修服务说明", content="保修政策：\n- 手表类：24个月保修\n- 耳机类：12个月保修\n- 配件类：6个月保修\n- 保修范围：非人为损坏的质量问题\n- 不在保修范围：进水、摔坏、私自拆修", category="technical", tags='["保修","售后"]'),
        ]
        session.add_all(articles)

        await session.commit()
        print("✅ 测试数据填充完成！")
        print(f"  - 商品: {len(products)} 个")
        print(f"  - 客户: {len(customers)} 个")
        print(f"  - 订单: {len(orders)} 个")
        print(f"  - 发票: {len(invoices)} 个")
        print(f"  - 退款: {len(refunds)} 条")
        print(f"  - 工单: {len(tickets)} 条")
        print(f"  - 知识库: {len(articles)} 篇")


if __name__ == "__main__":
    asyncio.run(seed_database())
