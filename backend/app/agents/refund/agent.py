from __future__ import annotations

import structlog
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from backend.app.agents.base import BaseAgent
from backend.app.services.llm.provider import LLMProvider
from backend.app.tools.refund.tools import order_lookup, process_refund, refund_eligibility

logger = structlog.get_logger()

SYSTEM_PROMPT = """你是退款客服Agent。职责：处理退款请求。

工作流程：
1. 查询客户订单
2. 检查退款资格
3. 告知用户结果

退款政策：30天内可退，质量问题可退，3-5个工作日到账。
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
        # 添加系统提示
        system_message = SystemMessage(content=SYSTEM_PROMPT)
        prompt_messages = [system_message] + list(messages)

        # 使用 function calling 执行工具
        return await self._invoke_and_execute_tools(prompt_messages, self.get_tools())
