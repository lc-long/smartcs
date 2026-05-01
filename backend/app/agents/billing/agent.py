from __future__ import annotations

import re

import structlog
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from backend.app.agents.base import BaseAgent
from backend.app.services.llm.provider import LLMProvider
from backend.app.tools.billing.tools import billing_summary, invoice_lookup, payment_history

logger = structlog.get_logger()

SYSTEM_PROMPT = """你是账单客服Agent。根据工具查询结果回复用户。
用中文回复，语气专业友好。"""


class BillingAgent(BaseAgent):
    name = "billing"
    description = "处理发票查询、支付历史、账单问题"

    def __init__(self, llm_provider: LLMProvider):
        super().__init__(
            llm_provider=llm_provider,
            temperature=0.3,
        )

    def get_tools(self):
        return [invoice_lookup, payment_history, billing_summary]

    def get_system_prompt(self):
        return SYSTEM_PROMPT

    async def run(self, messages: list[BaseMessage], **kwargs) -> AIMessage:
        user_text = " ".join(
            m.content if hasattr(m, "content") else str(m)
            for m in messages
        )

        customer_id = self._extract_customer_id(user_text)

        tool_results = []

        if customer_id:
            invoices = await invoice_lookup.ainvoke({"customer_id": customer_id})
            tool_results.append(f"发票信息：\n{invoices}")

            summary = await billing_summary.ainvoke({"customer_id": customer_id})
            tool_results.append(f"账单汇总：\n{summary}")

        if tool_results:
            context = "\n\n".join(tool_results)
            prompt = f"""你是账单客服Agent。根据以下查询结果回复用户。

用户问题：{user_text}

查询结果：
{context}

请用清晰的语言解释账单信息。用中文回复。"""

            response = await self.llm.ainvoke([
                SystemMessage(content=prompt),
                HumanMessage(content="请根据以上信息回复用户"),
            ])
            return response
        else:
            return AIMessage(content="请提供客户ID，以便我查询您的账单信息。")

    def _extract_customer_id(self, text: str) -> str | None:
        match = re.search(r'C\d{3}', text)
        return match.group() if match else None
