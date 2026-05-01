from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.tools import BaseTool

from backend.app.services.llm.provider import LLMProvider

logger = structlog.get_logger()


class BaseAgent(ABC):
    name: str = ""
    description: str = ""

    def __init__(
        self,
        llm_provider: LLMProvider,
        model_name: str | None = None,
        temperature: float = 0.3,
    ):
        self.llm_provider = llm_provider
        self._model_name = model_name
        self._temperature = temperature
        self._llm: BaseChatModel | None = None

    @property
    def llm(self) -> BaseChatModel:
        if self._llm is None:
            self._llm = self.llm_provider.get_llm(
                model_name=self._model_name,
                temperature=self._temperature,
            )
        return self._llm

    @abstractmethod
    async def run(self, messages: list[BaseMessage], **kwargs: Any) -> AIMessage:
        ...

    def get_tools(self) -> list[BaseTool]:
        return []

    def get_system_prompt(self) -> str:
        return f"你是{self.name}客服Agent。{self.description}"

    async def _invoke_with_tools(
        self,
        messages: list[BaseMessage],
        tools: list[BaseTool] | None = None,
    ) -> AIMessage:
        tools = tools or self.get_tools()
        start_time = time.time()

        logger.info(
            "agent_invoke_start",
            agent=self.name,
            message_count=len(messages),
            tool_count=len(tools),
        )

        try:
            if tools:
                llm_with_tools = self.llm.bind_tools(tools)
                response = await llm_with_tools.ainvoke(messages)
            else:
                response = await self.llm.ainvoke(messages)

            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(
                "agent_invoke_end",
                agent=self.name,
                latency_ms=elapsed_ms,
                has_tool_calls=bool(response.tool_calls),
            )
            return response

        except Exception:
            logger.exception("agent_invoke_error", agent=self.name)
            raise
