from __future__ import annotations

import json
import re

import structlog
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from backend.app.agents.base import BaseAgent
from backend.app.services.llm.provider import LLMProvider
from backend.app.tools.refund.tools import order_lookup, process_refund, refund_eligibility

logger = structlog.get_logger()

SYSTEM_PROMPT = """你是退款客服Agent。根据工具查询结果回复用户。
用中文回复，语气专业友好。"""


class RefundAgent(BaseAgent):
    name = "refund"
    description = "处理退款申请、订单查询、退款资格检查"

    def __init__(self, llm_provider: LLMProvider):
        super().__init__(
            llm_provider=llm_provider,
            temperature=0.3,
        )

    def get_tools(self):
        return [order_lookup, refund_eligibility, process_refund]

    def get_system_prompt(self):
        return SYSTEM_PROMPT

    async def run(self, messages: list[BaseMessage], **kwargs) -> AIMessage:
        # 提取用户信息
        user_text = " ".join(
            m.content if hasattr(m, "content") else str(m)
            for m in messages
        )

        # 提取客户ID和订单号
        customer_id = self._extract_customer_id(user_text)
        order_no = self._extract_order_no(user_text)

        # 直接调用工具获取数据
        tool_results = []

        if customer_id:
            orders_result = await order_lookup.ainvoke({"customer_id": customer_id})
            tool_results.append(f"订单查询结果：\n{orders_result}")

        if order_no:
            eligibility_result = await refund_eligibility.ainvoke({"order_no": order_no})
            tool_results.append(f"退款资格检查：\n{eligibility_result}")

        # 构建回复
        if tool_results:
            context = "\n\n".join(tool_results)
            prompt = f"""你是退款客服Agent。根据以下工具查询结果回复用户。

用户问题：{user_text}

工具查询结果：
{context}

请根据以上信息：
1. 确认订单信息
2. 说明退款资格
3. 如果符合退款条件，询问用户是否提交退款申请
4. 如果不符合，解释原因

用中文回复，语气专业友好。"""

            response = await self.llm.ainvoke([
                SystemMessage(content=prompt),
                HumanMessage(content="请根据以上信息回复用户"),
            ])
            return response
        else:
            return AIMessage(content="请提供客户ID或订单号，以便我查询您的退款信息。")

    def _extract_customer_id(self, text: str) -> str | None:
        """提取客户ID"""
        match = re.search(r'C\d{3}', text)
        return match.group() if match else None

    def _extract_order_no(self, text: str) -> str | None:
        """提取订单号"""
        match = re.search(r'ORD-\d{8}-\d{3}', text)
        return match.group() if match else None
