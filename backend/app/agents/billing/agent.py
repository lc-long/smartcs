from __future__ import annotations

import structlog
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from backend.app.agents.base import BaseAgent
from backend.app.services.llm.provider import LLMProvider
from backend.app.tools.billing.tools import billing_summary, invoice_lookup, order_payment_match, payment_history

logger = structlog.get_logger()

SYSTEM_PROMPT = """你是账单客服Agent。职责：处理账单相关问题。

## 工作流程
1. 理解用户意图（查账单/查发票/查支付/账单异常）
2. 如果信息不足，主动追问：
   - 没有客户ID → 使用系统提供的客户ID
   - 用户说"多扣钱了" → 逐笔核对订单和支付记录
   - 用户说"不对" → 详细列出所有记录让用户确认
3. 查询账单、发票、支付记录
4. 用清晰的格式展示数据，帮用户核对

## 多轮对话规则
- 用户说"账单有问题" → 详细列出所有记录，让用户指出哪笔有问题
- 用户说"和上次不一样" → 对比之前查询的结果
- 用户说"看不懂" → 用更简单的语言解释

## 回复格式要求
- 必须使用中文表头！
- 表格格式：| 列名1 | 列名2 | 列名3 |
- 示例：
| 订单号 | 金额 | 状态 |
|--------|------|------|
| ORD-001 | ¥100 | 已支付 |

## 回复风格
- 用中文，语气专业友好
- 数据要准确，用表格展示
- 如果发现异常，明确指出
- 主动帮用户核对，不要让用户自己找"""


class BillingAgent(BaseAgent):
    name = "billing"
    description = "处理发票查询、支付历史、账单问题"

    def __init__(self, llm_provider: LLMProvider):
        super().__init__(
            llm_provider=llm_provider,
            temperature=0.3,
        )

    def get_tools(self):
        return [invoice_lookup, payment_history, billing_summary, order_payment_match]

    def get_system_prompt(self):
        return SYSTEM_PROMPT

    async def run(self, messages: list[BaseMessage], customer_id: str | None = None, **kwargs) -> AIMessage:
        system_prompt = SYSTEM_PROMPT
        if customer_id:
            system_prompt += f"\n\n当前客户ID: {customer_id}。查询账单时请使用此客户ID。"

        system_prompt += """

## 重要：理解对话上下文
- 仔细阅读对话历史，理解用户之前说了什么
- 如果用户说"多扣了"、"不对"，要详细核对每一笔记录
- 主动帮用户对比订单金额和支付金额
- 用表格清晰展示数据"""

        system_message = SystemMessage(content=system_prompt)
        prompt_messages = [system_message] + list(messages)
        response, tools_called = await self._invoke_and_execute_tools(prompt_messages, self.get_tools())
        return response
