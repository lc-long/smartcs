from __future__ import annotations

import structlog
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from backend.app.agents.base import BaseAgent
from backend.app.services.llm.provider import LLMProvider
from backend.app.tools.advanced.tools import product_review_lookup
from backend.app.tools.technical.tools import (
    knowledge_search,
    product_info,
    ticket_create,
    ticket_lookup,
)

logger = structlog.get_logger()

SYSTEM_PROMPT = """你是技术支持Agent。职责：解决产品技术问题。

## 工作流程
1. 理解用户问题（设备故障/使用问题/产品咨询）
2. 搜索知识库找解决方案
3. 如果知识库没有，提供通用排查步骤
4. 如果问题复杂，建议创建工单或转人工

## 多轮对话规则
- 用户说"不好使" → 追问具体什么功能不好使
- 用户说"试过了" → 问试过什么方法，然后提供其他方案
- 用户说"还是不行" → 建议创建工单或转人工
- 用户描述多个问题 → 逐一处理，不要遗漏

## 问题排查逻辑
1. 先确认问题现象
2. 搜索知识库
3. 提供解决方案
4. 如果解决不了，创建工单

## 回复风格
- 用中文，语气专业耐心
- 步骤要清晰，易于操作
- 如果需要创建工单，说明原因和预期时间"""


class TechnicalAgent(BaseAgent):
    name = "technical"
    description = "处理产品故障排查、FAQ搜索、技术支持"

    def __init__(self, llm_provider: LLMProvider):
        super().__init__(
            llm_provider=llm_provider,
            temperature=0.3,
        )

    def get_tools(self):
        return [knowledge_search, ticket_create, ticket_lookup, product_info, product_review_lookup]

    def get_system_prompt(self):
        return SYSTEM_PROMPT

    async def run(self, messages: list[BaseMessage], customer_id: str | None = None, **kwargs) -> AIMessage:
        system_prompt = SYSTEM_PROMPT
        if customer_id:
            system_prompt += f"\n\n当前客户ID: {customer_id}。创建工单时请使用此客户ID。"

        system_prompt += """

## 重要：理解对话上下文
- 仔细阅读对话历史，理解用户之前说了什么
- 如果用户说"试过了"，问清楚试过什么
- 如果用户说"还是不行"，建议创建工单
- 提供的解决方案要具体、可操作"""

        system_message = SystemMessage(content=system_prompt)
        prompt_messages = [system_message] + list(messages)
        return await self._invoke_and_execute_tools(prompt_messages, self.get_tools())
