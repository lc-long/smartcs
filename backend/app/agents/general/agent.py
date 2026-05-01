from __future__ import annotations

import structlog
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from backend.app.agents.base import BaseAgent
from backend.app.services.llm.provider import LLMProvider
from backend.app.tools.general.tools import company_info, faq_search

logger = structlog.get_logger()

SYSTEM_PROMPT = """你是一个通用客服Agent。你的职责是处理无法归类到其他专业领域的通用咨询。

## 你能做的事情
- 搜索常见问题FAQ
- 提供公司基本信息
- 解答通用的产品咨询
- 引导客户到合适的专业Agent

## 工作原则
1. 尽量从FAQ中找到答案
2. 如果问题属于账单、技术或退款范畴，告知客户可以转接专业客服
3. 不要编造信息，只基于工具返回的数据回答

## 回复风格
- 热情友好
- 简洁明了
- 主动提供帮助"""


class GeneralAgent(BaseAgent):
    name = "general"
    description = "处理通用咨询、FAQ搜索、公司信息查询"

    def __init__(self, llm_provider: LLMProvider):
        super().__init__(
            llm_provider=llm_provider,
            temperature=0.3,
        )

    def get_tools(self):
        return [faq_search, company_info]

    def get_system_prompt(self):
        return SYSTEM_PROMPT

    async def run(self, messages: list[BaseMessage], **kwargs) -> AIMessage:
        prompt_messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        return await self._invoke_with_tools(prompt_messages, self.get_tools())
