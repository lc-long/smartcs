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

工作流程：
1. 了解用户问题
2. 搜索知识库找解决方案
3. 如果需要，创建技术支持工单
4. 提供产品信息

用中文回复，语气专业友好。"""


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
        system_message = SystemMessage(content=SYSTEM_PROMPT)
        prompt_messages = [system_message] + list(messages)
        return await self._invoke_and_execute_tools(prompt_messages, self.get_tools())
