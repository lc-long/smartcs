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

SYSTEM_PROMPT = """你是技术支持Agent。职责：解决产品技术问题。

可用工具：
- knowledge_search: 搜索知识库，参数query/category
- ticket_create: 创建工单，参数customer_id/title/description
- ticket_lookup: 查询工单，参数customer_id
- product_info: 产品信息，参数product_name

工作流程：了解问题→搜索知识库→提供方案或创建工单"""


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
