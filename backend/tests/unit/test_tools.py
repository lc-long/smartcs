from __future__ import annotations

import pytest
from backend.app.tools.billing.tools import invoice_lookup, payment_history, billing_summary
from backend.app.tools.technical.tools import knowledge_search, product_info
from backend.app.tools.refund.tools import order_lookup, refund_eligibility, process_refund
from backend.app.tools.general.tools import faq_search, company_info


class TestBillingTools:
    @pytest.mark.asyncio
    async def test_invoice_lookup_found(self):
        result = await invoice_lookup.ainvoke({"customer_id": "C001"})
        assert "299" in result
        assert "paid" in result

    @pytest.mark.asyncio
    async def test_invoice_lookup_not_found(self):
        result = await invoice_lookup.ainvoke({"customer_id": "C999"})
        assert "未找到" in result

    @pytest.mark.asyncio
    async def test_payment_history(self):
        result = await payment_history.ainvoke({"customer_id": "C001"})
        assert "支付宝" in result or "微信" in result

    @pytest.mark.asyncio
    async def test_billing_summary(self):
        result = await billing_summary.ainvoke({"customer_id": "C001"})
        assert "基础套餐" in result


class TestTechnicalTools:
    @pytest.mark.asyncio
    async def test_knowledge_search(self):
        result = await knowledge_search.ainvoke({"query": "无法开机"})
        assert "故障排查" in result or "电源" in result

    @pytest.mark.asyncio
    async def test_product_info_list(self):
        result = await product_info.ainvoke({})
        assert "智能手表" in result or "智能手环" in result

    @pytest.mark.asyncio
    async def test_product_info_specific(self):
        result = await product_info.ainvoke({"product_name": "智能手表Pro"})
        assert "1999" in result


class TestRefundTools:
    @pytest.mark.asyncio
    async def test_order_lookup_by_id(self):
        result = await order_lookup.ainvoke({"order_id": "ORD001"})
        assert "智能手表Pro" in result

    @pytest.mark.asyncio
    async def test_order_lookup_not_found(self):
        result = await order_lookup.ainvoke({"order_id": "ORD999"})
        assert "未找到" in result

    @pytest.mark.asyncio
    async def test_refund_eligibility(self):
        result = await refund_eligibility.ainvoke({"order_id": "ORD001"})
        assert "eligible" in result

    @pytest.mark.asyncio
    async def test_process_refund(self):
        result = await process_refund.ainvoke({
            "order_id": "ORD001",
            "reason": "商品质量问题",
        })
        assert "RF-" in result
        assert "pending_approval" in result


class TestGeneralTools:
    @pytest.mark.asyncio
    async def test_faq_search(self):
        result = await faq_search.ainvoke({"query": "密码"})
        assert "重置密码" in result

    @pytest.mark.asyncio
    async def test_company_info(self):
        result = await company_info.ainvoke({"info_type": "contact"})
        assert "400" in result
