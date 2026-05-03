from __future__ import annotations

import structlog
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from backend.app.services.llm.provider import get_llm_provider

logger = structlog.get_logger()

MAX_HISTORY_MESSAGES = 20
SUMMARY_THRESHOLD = 15


class ConversationSummarizer:
    def __init__(self):
        self.llm_provider = get_llm_provider()

    async def summarize_if_needed(self, messages: list[BaseMessage]) -> tuple[list[BaseMessage], str | None]:
        if len(messages) <= MAX_HISTORY_MESSAGES:
            return messages, None

        summary = await self.summarize(messages)
        summarized_messages = await self.compress_history(messages, summary)
        return summarized_messages, summary

    async def summarize(self, messages: list[BaseMessage]) -> str:
        conversation_text = self._format_messages(messages)
        summary_prompt = f"""请简要总结以下对话的核心内容，保留关键信息（用户问题、已确认的信息、当前进度）：

{conversation_text}

格式：
## 对话摘要
- 用户意图：...
- 已确认信息：...
- 当前进度：...
- 待解决问题：...

请用中文回答："""

        try:
            llm = self.llm_provider.get_llm(temperature=0.3)
            response = await llm.ainvoke([HumanMessage(content=summary_prompt)])
            summary = response.content if isinstance(response.content, str) else str(response.content)
            logger.info("conversation_summarized", original_len=len(messages), summary_len=len(summary))
            return summary
        except Exception as e:
            logger.warning("summarization_failed", error=str(e))
            return "[对话过长，已省略早期内容]"

    async def compress_history(
        self,
        messages: list[BaseMessage],
        summary: str,
    ) -> list[BaseMessage]:
        recent_messages = messages[-5:] if len(messages) > 5 else messages
        summary_message = AIMessage(
            content=f"[早期对话摘要]\n{summary}\n[/早期对话摘要]"
        )
        return [summary_message] + list(recent_messages)

    def _format_messages(self, messages: list[BaseMessage]) -> str:
        formatted = []
        for m in messages[-30:]:
            role = "用户" if isinstance(m, HumanMessage) else "客服"
            content = m.content if hasattr(m, "content") else str(m)
            formatted.append(f"{role}：{content[:200]}")
        return "\n".join(formatted)


_summarizer: ConversationSummarizer | None = None


def get_summarizer() -> ConversationSummarizer:
    global _summarizer
    if _summarizer is None:
        _summarizer = ConversationSummarizer()
    return _summarizer
