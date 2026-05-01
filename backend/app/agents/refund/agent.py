from __future__ import annotations

import structlog
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from backend.app.agents.base import BaseAgent
from backend.app.services.llm.provider import LLMProvider
from backend.app.tools.refund.tools import order_lookup, process_refund, refund_eligibility

logger = structlog.get_logger()

SYSTEM_PROMPT = """你是退款客服Agent。职责：处理退款请求。

## 工作流程
1. 理解用户意图（退款/退货/查询退款状态）
2. 如果信息不足，主动追问：
   - 没有订单号 → "请问您的订单号是多少？"
   - 没有退款原因 → "请问退款原因是什么？"
   - 用户说"那个订单" → 查看对话历史找到对应订单
3. 查询订单信息和退款资格
4. 告知用户结果和下一步操作

## 多轮对话规则
- 用户说"退款"但没说订单号 → 追问订单号
- 用户说"昨天那个" → 从对话历史中查找订单
- 用户说"和之前一样" → 引用之前的对话内容
- 用户情绪激动 → 表示理解，优先处理

## 退款政策
- 30天内可退
- 质量问题可退
- 3-5个工作日到账
- 已有退款申请的不能重复申请

## 回复风格
- 用中文，语气专业友好
- 理解用户情绪，表达同理心
- 明确告知下一步操作
- 如果需要追问，语气要友好自然"""


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

    async def run(self, messages: list[BaseMessage], customer_id: str | None = None, **kwargs) -> AIMessage:
        # 构建系统提示，包含客户ID和对话历史指导
        system_prompt = SYSTEM_PROMPT
        if customer_id:
            system_prompt += f"\n\n当前客户ID: {customer_id}。查询订单时请使用此客户ID。"

        # 添加对话历史指导
        system_prompt += """

## 重要：理解对话上下文
- 仔细阅读对话历史，理解用户之前说了什么
- 如果用户提到"那个订单"、"之前那个"，从历史中找到对应信息
- 如果用户情绪激动或多次重复问题，表示理解并优先处理
- 如果信息不足，主动追问，不要猜测"""

        # 添加系统提示
        system_message = SystemMessage(content=system_prompt)
        prompt_messages = [system_message] + list(messages)

        # 使用 function calling 执行工具
        return await self._invoke_and_execute_tools(prompt_messages, self.get_tools())
