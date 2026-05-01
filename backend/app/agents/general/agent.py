from __future__ import annotations

import structlog
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from backend.app.agents.base import BaseAgent
from backend.app.services.llm.provider import LLMProvider
from backend.app.tools.general.tools import company_info, customer_info, faq_search

logger = structlog.get_logger()

SYSTEM_PROMPT = """你是通用客服Agent。根据工具查询结果回复用户。
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
        user_text = " ".join(
            m.content if hasattr(m, "content") else str(m)
            for m in messages
        )

        # 搜索FAQ
        faq = await faq_search.ainvoke({"query": user_text[:50]})

        context = f"FAQ搜索结果：\n{faq}"
        prompt = f"""你是通用客服Agent。根据以下信息回复用户。

用户问题：{user_text}

{context}

请用友好的语气回答用户问题。如果问题不属于你的范围，建议用户联系专业客服。用中文回复。"""

        response = await self.llm.ainvoke([SystemMessage(content=prompt)])
        return response
