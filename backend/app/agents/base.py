from __future__ import annotations

import re
import time
from abc import ABC, abstractmethod
from typing import Any

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
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
        """使用 function calling 调用工具"""
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
                # 使用 bind_tools 绑定工具
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

    async def _invoke_and_execute_tools(
        self,
        messages: list[BaseMessage],
        tools: list[BaseTool] | None = None,
        max_iterations: int = 5,
    ) -> AIMessage:
        """调用 LLM 并执行工具调用（ReAct 风格）"""
        tools = tools or self.get_tools()
        tool_map = {t.name: t for t in tools}

        current_messages = list(messages)
        last_response = None

        for i in range(max_iterations):
            # 调用 LLM
            response = await self._invoke_with_tools(current_messages, tools)
            last_response = response

            # 如果没有工具调用，返回结果
            if not response.tool_calls:
                return response

            # 执行工具调用
            tool_results = []
            for tc in response.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                tool_id = tc["id"]

                logger.info(
                    "tool_call",
                    agent=self.name,
                    tool=tool_name,
                    args=tool_args,
                )

                # 执行工具
                tool = tool_map.get(tool_name)
                if tool:
                    try:
                        result = await tool.ainvoke(tool_args)
                        tool_results.append({
                            "tool_call_id": tool_id,
                            "role": "tool",
                            "content": str(result),
                        })
                    except Exception as e:
                        tool_results.append({
                            "tool_call_id": tool_id,
                            "role": "tool",
                            "content": f"工具执行失败: {str(e)}",
                        })
                else:
                    tool_results.append({
                        "tool_call_id": tool_id,
                        "role": "tool",
                        "content": f"未知工具: {tool_name}",
                    })

            # 将工具结果添加到消息中
            current_messages.append(response)
            current_messages.extend(tool_results)

        return last_response
