from __future__ import annotations

import structlog
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from backend.app.agents.base import BaseAgent
from backend.app.services.llm.provider import LLMProvider
from backend.app.tools.billing.tools import billing_summary, invoice_lookup, payment_history

logger = structlog.get_logger()

SYSTEM_PROMPT = """你是账单客服Agent。职责：处理账单相关问题。

工作流程：
1. 确认客户ID
2. 查询发票和账单信息
3. 用清晰的语言解释账单

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
        system_message = SystemMessage(content=SYSTEM_PROMPT)
        prompt_messages = [system_message] + list(messages)
        return await self._invoke_and_execute_tools(prompt_messages, self.get_tools())
