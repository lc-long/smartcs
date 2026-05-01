from __future__ import annotations

import structlog
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from backend.app.agents.base import BaseAgent
from backend.app.services.llm.provider import LLMProvider
from backend.app.tools.general.tools import company_info, customer_info, faq_search

logger = structlog.get_logger()

SYSTEM_PROMPT = """你是通用客服Agent。职责：处理通用咨询。

工作流程：
1. 理解用户问题
2. 搜索FAQ或查询公司信息
3. 用友好的语气回答

如果问题属于账单、技术或退款范畴，建议用户联系专业客服。
用中文回复，语气热情友好。"""


class GeneralAgent(BaseAgent):
    name = "general"
    description = "处理通用咨询、FAQ搜索、公司信息查询"

    def __init__(self, llm_provider: LLMProvider):
        super().__init__(
            llm_provider=llm_provider,
            temperature=0.3,
        )

    def get_tools(self):
        return [faq_search, company_info, customer_info]

    def get_system_prompt(self):
        return SYSTEM_PROMPT

    async def run(self, messages: list[BaseMessage], **kwargs) -> AIMessage:
        system_message = SystemMessage(content=SYSTEM_PROMPT)
        prompt_messages = [system_message] + list(messages)
        return await self._invoke_and_execute_tools(prompt_messages, self.get_tools())
