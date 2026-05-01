from __future__ import annotations

import re

import structlog
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from backend.app.agents.base import BaseAgent
from backend.app.services.llm.provider import LLMProvider
from backend.app.tools.technical.tools import (
    knowledge_search,
    product_info,
    ticket_create,
    ticket_lookup,
)

logger = structlog.get_logger()

SYSTEM_PROMPT = """你是技术支持Agent。根据工具查询结果回复用户。
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
        # 提取最后一条用户消息
        user_text = ""
        for msg in reversed(messages):
            if hasattr(msg, "content") and isinstance(msg.content, str) and msg.content.strip():
                user_text = msg.content
                break

        # 搜索知识库
        search_query = self._extract_search_query(user_text)
        knowledge = await knowledge_search.ainvoke({"query": search_query})

        # 查询产品信息
        product_name = self._extract_product_name(user_text)
        product = None
        if product_name:
            product = await product_info.ainvoke({"product_name": product_name})

        tool_results = [f"知识库搜索：\n{knowledge}"]
        if product:
            tool_results.append(f"产品信息：\n{product}")

        context = "\n\n".join(tool_results)
        prompt = f"""你是技术支持Agent。根据以下信息回复用户。

用户问题：{user_text}

查询结果：
{context}

请根据知识库内容提供解决方案。如果问题复杂，建议创建工单。用中文回复。"""

        response = await self.llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content="请根据以上信息回复用户"),
        ])
        return response

    def _extract_search_query(self, text: str) -> str:
        """提取搜索关键词"""
        # 移除常见停用词
        stop_words = ["我", "的", "是", "有", "想", "要", "怎么", "什么", "如何", "请", "帮", "查"]
        words = text
        for word in stop_words:
            words = words.replace(word, " ")
        return words.strip()[:50]

    def _extract_product_name(self, text: str) -> str | None:
        """提取产品名称"""
        products = ["智能手表Pro", "智能手表Lite", "智能手环Pro", "智能手环Lite", "降噪耳机Pro", "无线耳机Lite", "无线充电器", "表带套装"]
        for product in products:
            if product in text:
                return product
        return None
