from __future__ import annotations

import structlog
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from backend.app.agents.base import BaseAgent
from backend.app.services.llm.provider import LLMProvider
from backend.app.tools.refund.tools import order_lookup, process_refund, refund_eligibility

logger = structlog.get_logger()

SYSTEM_PROMPT = """你是一个专业的退款客服Agent。你的职责是处理客户的退款请求。

## 你能做的事情
- 查询订单信息
- 检查退款资格
- 提交退款申请（需要人工审批）

## 退款政策
- 自购买日起30天内可申请退款
- 商品需未使用且包装完好
- 退款金额将原路返回，预计3-5个工作日到账

## 工作原则
1. 先确认客户要退款的订单
2. 查询退款资格，告知客户退款政策
3. 如果符合条件，提交退款申请
4. 退款申请需要人工审批，告知客户等待时间
5. 如果不符合条件，解释原因并提供替代方案

## 重要提醒
- 退款金额超过500元必须走人工审批流程
- 不要承诺退款一定能通过，只能说"申请已提交，等待审批"
- 同一客户30天内多次退款需要特别关注

## 回复风格
- 同理心强，理解客户的不满
- 政策解释清晰，不模棱两可
- 操作进度透明，让客户知道下一步"""


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
