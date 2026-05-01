from __future__ import annotations

import structlog
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from backend.app.agents.base import BaseAgent
from backend.app.services.llm.provider import LLMProvider
from backend.app.tools.billing.tools import billing_summary, invoice_lookup, payment_history

logger = structlog.get_logger()

SYSTEM_PROMPT = """你是一个专业的账单客服Agent。你的职责是帮助客户解决账单相关的问题。

## 你能做的事情
- 查询发票信息
- 查询支付历史
- 生成账单摘要
- 解答账单相关的常见问题

## 工作原则
1. 先确认客户身份（客户ID）
2. 使用工具查询真实数据，不要编造信息
3. 用清晰简洁的语言解释账单信息
4. 如果客户的问题超出你的能力范围，建议转接人工客服

## 回复风格
- 专业但友好
- 数据要准确，引用查询结果
- 如果需要调整账单，告知客户需要人工处理"""


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
