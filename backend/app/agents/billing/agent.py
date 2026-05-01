from __future__ import annotations

import structlog
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from backend.app.agents.base import BaseAgent
from backend.app.services.llm.provider import LLMProvider
from backend.app.tools.billing.tools import billing_summary, invoice_lookup, payment_history

logger = structlog.get_logger()

SYSTEM_PROMPT = """你是账单客服Agent。职责：处理账单相关问题。

可用工具：
- invoice_lookup: 查询发票，参数customer_id/status
- payment_history: 查询支付记录，参数customer_id
- billing_summary: 账单汇总，参数customer_id

工作流程：先确认客户ID→查询数据→回复"""


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
        prompt_messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        return await self._invoke_with_tools(prompt_messages, self.get_tools())
