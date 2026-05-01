from __future__ import annotations

import structlog
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from backend.app.agents.base import BaseAgent
from backend.app.services.llm.provider import LLMProvider
from backend.app.tools.advanced.tools import (
    customer_coupon_lookup,
    customer_feedback_lookup,
    loyalty_points_lookup,
    product_recommendation,
    shipment_tracking,
)
from backend.app.tools.general.tools import company_info, customer_info, faq_search
from backend.app.tools.refund.tools import order_lookup

logger = structlog.get_logger()

SYSTEM_PROMPT = """你是通用客服Agent。职责：处理通用咨询和协调。

## 工作流程
1. 理解用户意图
2. 如果是简单问题，直接回答
3. 如果需要其他Agent协助，说明会转接
4. 如果信息不足，主动追问

## 你可以处理的问题类型
- **订单查询**：查询订单列表、订单详情
- **物流追踪**：查询包裹物流状态、追踪记录
- **积分查询**：查询积分余额、积分历史、积分规则
- **优惠券**：查询可用优惠券、使用规则
- **产品推荐**：根据需求推荐合适的产品
- **客户反馈**：查询反馈记录、提交新反馈
- **公司信息**：查询公司政策、服务说明
- **FAQ**：搜索常见问题解答

## 多轮对话规则
- 用户说"帮我查一下" → 追问具体查什么
- 用户说"那个" → 从对话历史找对应信息
- 用户说"算了" → 确认是否放弃，不要直接结束
- 用户说"转人工" → 确认原因，然后转接
- 用户问积分 → 查询积分并解释积分规则
- 用户问物流 → 查询物流并告知最新状态

## 回复风格
- 用中文，语气热情友好
- 主动提供帮助
- 如果需要转接，说明原因
- 数据用表格展示，清晰易读"""


class GeneralAgent(BaseAgent):
    name = "general"
    description = "处理通用咨询、FAQ搜索、公司信息查询"

    def __init__(self, llm_provider: LLMProvider):
        super().__init__(
            llm_provider=llm_provider,
            temperature=0.3,
        )

    def get_tools(self):
        return [
            faq_search, company_info, customer_info, order_lookup,
            shipment_tracking, loyalty_points_lookup, customer_coupon_lookup,
            product_recommendation, customer_feedback_lookup,
        ]

    def get_system_prompt(self):
        return SYSTEM_PROMPT

    async def run(self, messages: list[BaseMessage], customer_id: str | None = None, **kwargs) -> AIMessage:
        system_prompt = SYSTEM_PROMPT
        if customer_id:
            system_prompt += f"\n\n当前客户ID: {customer_id}。查询客户信息时请使用此客户ID。"

        system_prompt += """

## 重要：理解对话上下文
- 仔细阅读对话历史，理解用户之前说了什么
- 如果用户提到"那个订单"、"之前那个"，从历史中找
- 主动理解用户意图，不要等用户说完整句话"""

        system_message = SystemMessage(content=system_prompt)
        prompt_messages = [system_message] + list(messages)
        return await self._invoke_and_execute_tools(prompt_messages, self.get_tools())
