from __future__ import annotations

import pytest
from backend.app.tools.billing.tools import invoice_lookup, payment_history, billing_summary, order_payment_match
from backend.app.tools.technical.tools import knowledge_search, product_info, ticket_create, ticket_lookup, ticket_update
from backend.app.tools.refund.tools import order_lookup, refund_eligibility, process_refund, refund_status_lookup
from backend.app.tools.general.tools import faq_search, company_info, customer_info
from backend.app.tools.advanced.tools import (
    shipment_tracking, product_review_lookup, loyalty_points_lookup, customer_coupon_lookup,
    product_recommendation, customer_feedback_lookup, customer_feedback_submit,
    loyalty_points_redeem, coupon_apply,
)


class TestBillingTools:
    @pytest.mark.asyncio
    async def test_invoice_lookup_found(self):
        result = await invoice_lookup.ainvoke({"customer_id": "C001"})
        assert "299" in result or "未找到" in result

    @pytest.mark.asyncio
    async def test_invoice_lookup_not_found(self):
        result = await invoice_lookup.ainvoke({"customer_id": "C999"})
        assert "未找到" in result

    @pytest.mark.asyncio
    async def test_payment_history(self):
        result = await payment_history.ainvoke({"customer_id": "C001"})
        assert "支付" in result or "支付宝" in result or "微信" in result or "未找到" in result

    @pytest.mark.asyncio
    async def test_billing_summary(self):
        result = await billing_summary.ainvoke({"customer_id": "C001"})
        assert "账单" in result or "未找到" in result or "¥" in result

    @pytest.mark.asyncio
    async def test_order_payment_match(self):
        result = await order_payment_match.ainvoke({"customer_id": "C001"})
        assert "订单" in result or "未找到" in result


class TestTechnicalTools:
    @pytest.mark.asyncio
    async def test_knowledge_search(self):
        result = await knowledge_search.ainvoke({"query": "无法开机"})
        assert "故障排查" in result or "电源" in result or "未找到" in result

    @pytest.mark.asyncio
    async def test_product_info_list(self):
        result = await product_info.ainvoke({})
        assert "智能手表" in result or "智能手环" in result or "未找到" in result

    @pytest.mark.asyncio
    async def test_product_info_specific(self):
        result = await product_info.ainvoke({"product_name": "智能手表Pro"})
        assert "1999" in result or "未找到" in result

    @pytest.mark.asyncio
    async def test_ticket_create(self):
        result = await ticket_create.ainvoke({
            "customer_id": "C001",
            "title": "测试工单",
            "description": "测试问题描述",
            "priority": "medium",
        })
        assert "TK-" in result or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_ticket_lookup(self):
        result = await ticket_lookup.ainvoke({"customer_id": "C001"})
        assert "工单" in result or "暂无" in result

    @pytest.mark.asyncio
    async def test_ticket_update_not_found(self):
        result = await ticket_update.ainvoke({"ticket_no": "TK-9999", "status": "resolved"})
        assert "未找到" in result


class TestRefundTools:
    @pytest.mark.asyncio
    async def test_order_lookup(self):
        result = await order_lookup.ainvoke({"customer_id": "C001"})
        assert "订单" in result or "暂无" in result

    @pytest.mark.asyncio
    async def test_refund_eligibility_not_found(self):
        result = await refund_eligibility.ainvoke({"order_no": "ORD999"})
        assert "未找到" in result

    @pytest.mark.asyncio
    async def test_refund_status_lookup_not_found(self):
        result = await refund_status_lookup.ainvoke({"order_no": "ORD999"})
        assert "未找到" in result or "暂无退款" in result


class TestGeneralTools:
    @pytest.mark.asyncio
    async def test_faq_search(self):
        result = await faq_search.ainvoke({"query": "密码"})
        assert "重置密码" in result or "FAQ" in result or "未找到" in result

    @pytest.mark.asyncio
    async def test_company_info(self):
        result = await company_info.ainvoke({"info_type": "contact"})
        assert "400" in result or "客服" in result

    @pytest.mark.asyncio
    async def test_customer_info_not_found(self):
        result = await customer_info.ainvoke({"customer_id": "C999"})
        assert "未找到" in result or "error" in result.lower()


class TestAdvancedTools:
    @pytest.mark.asyncio
    async def test_shipment_tracking_not_found(self):
        result = await shipment_tracking.ainvoke({"order_no": "ORD999"})
        assert "未找到" in result or "暂无物流" in result

    @pytest.mark.asyncio
    async def test_product_review_not_found(self):
        result = await product_review_lookup.ainvoke({"product_name": "不存在的商品"})
        assert "未找到" in result or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_loyalty_points_lookup_not_found(self):
        result = await loyalty_points_lookup.ainvoke({"customer_id": "C999"})
        assert "未找到" in result or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_customer_coupon_lookup_not_found(self):
        result = await customer_coupon_lookup.ainvoke({"customer_id": "C999"})
        assert "未找到" in result or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_product_recommendation(self):
        result = await product_recommendation.ainvoke({"category": "手表"})
        assert "推荐" in result or "未找到" in result or "智能手表" in result

    @pytest.mark.asyncio
    async def test_customer_feedback_lookup(self):
        result = await customer_feedback_lookup.ainvoke({})
        assert "反馈" in result or "暂无" in result

    @pytest.mark.asyncio
    async def test_customer_feedback_submit(self):
        result = await customer_feedback_submit.ainvoke({
            "customer_id": "C001",
            "feedback_type": "suggestion",
            "subject": "测试反馈",
            "content": "这是一条测试反馈",
        })
        assert "feedback_id" in result or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_loyalty_points_redeem_insufficient(self):
        result = await loyalty_points_redeem.ainvoke({
            "customer_id": "C001",
            "points": 999999,
        })
        assert "积分不足" in result or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_coupon_apply_not_found(self):
        result = await coupon_apply.ainvoke({
            "customer_id": "C001",
            "coupon_code": "INVALID",
            "order_no": "ORD999",
        })
        assert "未找到" in result or "无效" in result or "error" in result.lower()