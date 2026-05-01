from __future__ import annotations

import structlog
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from backend.app.agents.base import BaseAgent
from backend.app.services.llm.provider import LLMProvider
from backend.app.tools.technical.tools import (
    knowledge_search,
    product_info,
    ticket_create,
    ticket_lookup,
)

logger = structlog.get_logger()

SYSTEM_PROMPT = """你是一个专业的技术支持Agent。你的职责是帮助客户解决产品使用和技术问题。

## 你能做的事情
- 从知识库搜索解决方案
- 查询和创建技术工单
- 提供产品信息和使用指导
- 排查常见技术故障

## 工作原则
1. 先了解客户遇到的具体问题
2. 优先从知识库搜索已有解决方案
3. 如果已有方案无法解决，创建技术工单
4. 复杂问题建议转接高级技术支持

## 排查流程
1. 确认问题现象
2. 搜索知识库
3. 提供解决方案
4. 如果解决不了，创建工单并告知客户处理时间

## 回复风格
- 条理清晰，步骤明确
- 使用客户能理解的语言，避免专业术语
- 引用知识库内容时注明来源"""


class TechnicalAgent(BaseAgent):
    name = "technical"
    description = "处理产品故障排查、FAQ搜索、技术支持"

    def __init__(self, llm_provider: LLMProvider):
        super().__init__(
            llm_provider=llm_provider,
            temperature=0.3,
        )

    def get_tools(self):
        return [knowledge_search, ticket_create, ticket_lookup, product_info]

    def get_system_prompt(self):
        return SYSTEM_PROMPT

    async def run(self, messages: list[BaseMessage], **kwargs) -> AIMessage:
        prompt_messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        return await self._invoke_with_tools(prompt_messages, self.get_tools())
