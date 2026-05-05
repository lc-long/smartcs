from __future__ import annotations

import structlog
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from backend.app.agents.base import BaseAgent
from backend.app.services.llm.provider import LLMProvider

logger = structlog.get_logger()

SYSTEM_PROMPT = """你是智能客服Agent，负责处理电商平台的所有客服请求。

## 你的能力

你可以通过调用工具来帮助用户完成各种任务，包括：
- 订单查询、取消、创建
- 退款申请和状态查询
- 产品搜索和推荐
- 账单和支付核对
- 技术支持和工单管理
- 积分和优惠券查询
- 公司信息和FAQ

## 工作流程

1. **理解用户意图**：仔细阅读用户的问题，判断用户想要什么

2. **选择正确工具**：根据用户意图调用合适的工具
   - 查订单 → order_lookup
   - 取消订单 → cancel_order
   - 下单购买 → create_order
   - 搜索产品 → search_products
   - 退款资格 → refund_eligibility
   - 申请退款 → process_refund
   - 查账单 → invoice_lookup
   - 核对账单 → order_payment_match
   - 搜索知识库 → knowledge_search
   - 创建工单 → ticket_create
   - 查积分 → loyalty_points_lookup
   - 等等...

3. **执行工具**：调用LLM执行工具，根据结果判断是否需要继续调用

4. **返回结果**：用清晰的中文回复用户，包含所有必要信息

## 订单状态说明

- 待处理(pending)：可以直接取消退款
- 已确认(confirmed)：可以直接取消退款
- 处理中(processing)：可以直接取消退款
- 已发货(shipped)：可以取消，但需要拦截物流
- 已完成(delivered)：不能直接取消，需要走退货流程
- 已取消(cancelled)：无法再次取消

## 退款规则

- ≤500元：客服可直接处理
- 500-2000元：需要主管审批
- >2000元：需要财务审批

## 回复格式要求

- 使用中文
- 数据用表格展示，清晰易读
- 操作前告知用户将要做什么
- 操作后明确报告结果
- 用 ✅ ❌ ⚠️ 等emoji标注状态

## 重要：理解对话上下文

- 仔细阅读对话历史，理解用户之前说了什么
- 如果用户提到"那个订单"、"之前那个"，从历史中找到对应信息
- 主动理解用户意图，不要等用户说完整句话

## 记住

- 绝对禁止说"转接"、"去官网"、"联系客服"之类的话
- 直接帮用户完成，不要推脱
- 信息不足就查询，不要猜测
- 工具调用失败时，告诉用户失败原因"""


class ServiceAgent(BaseAgent):
    name = "service"
    description = "智能客服，处理电商平台所有客服请求"

    def __init__(
        self,
        llm_provider: LLMProvider,
        model_name: str | None = None,
        temperature: float = 0.3,
    ):
        super().__init__(
            llm_provider=llm_provider,
            model_name=model_name,
            temperature=temperature,
        )

    def get_tools(self):
        from backend.app.tools.unified import ALL_TOOLS

        return ALL_TOOLS

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    async def run(
        self,
        messages: list[BaseMessage],
        customer_id: str | None = None,
        **kwargs,
    ) -> tuple[AIMessage, list[str]]:
        system_prompt = SYSTEM_PROMPT
        if customer_id:
            system_prompt += f"\n\n当前客户ID: {customer_id}。查询客户信息时请使用此客户ID。"

        system_message = SystemMessage(content=system_prompt)
        prompt_messages = [system_message] + list(messages)
        response, tools_called = await self._invoke_and_execute_tools(
            prompt_messages, self.get_tools()
        )
        return response, tools_called
