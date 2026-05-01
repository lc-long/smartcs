from __future__ import annotations

import structlog
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from backend.app.agents.base import BaseAgent
from backend.app.services.llm.provider import LLMProvider
from backend.app.tools.refund.tools import order_lookup, process_refund, refund_eligibility

logger = structlog.get_logger()

SYSTEM_PROMPT = """你是退款客服Agent。职责：处理退款请求。

可用工具：
- order_lookup: 查询订单，参数customer_id
- refund_eligibility: 检查退款资格，参数order_no
- process_refund: 提交退款，参数order_no/amount/reason

工作流程：先查订单→检查资格→提交退款（超500元需审批）
退款政策：30天内可退，3-5个工作日到账"""


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
        prompt_messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        return await self._invoke_with_tools(prompt_messages, self.get_tools())
