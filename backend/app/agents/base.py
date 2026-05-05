from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.tools import BaseTool

from backend.app.core.config.settings import get_settings
from backend.app.services.llm.provider import (
    LLMProvider,
    TokenUsage,
    estimate_cost,
    get_token_counter,
)

logger = structlog.get_logger()


class BaseAgent(ABC):
    name: str = ""
    description: str = ""
    intent_types: list[str] = []
    tools: list[str] = []

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
        self._settings = get_settings()

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

    def get_capability(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "intent_types": self.intent_types,
            "tools": self.tools,
        }

    async def _invoke_with_tools(
        self,
        messages: list[BaseMessage],
        tools: list[BaseTool] | None = None,
        timeout: float | None = None,
    ) -> AIMessage:
        """使用 function calling 调用工具，支持DeepSeek兜底"""
        tools = tools or self.get_tools()
        timeout = timeout or self._settings.agent_timeout_seconds
        start_time = time.time()

        logger.info(
            "agent_invoke_start",
            agent=self.name,
            message_count=len(messages),
            tool_count=len(tools),
            timeout=timeout,
        )

        # 尝试主LLM，失败后用DeepSeek兜底
        for attempt in range(2):
            try:
                if attempt == 0:
                    llm = self.llm
                    provider_name = "minimax"
                else:
                    # 使用DeepSeek兜底
                    llm = self.llm_provider._create_deepseek_llm("deepseek-chat", self._temperature)
                    provider_name = "deepseek"
                    logger.info("fallback_to_deepseek", agent=self.name)

                if tools:
                    llm_with_tools = llm.bind_tools(tools)
                    response = await asyncio.wait_for(
                        llm_with_tools.ainvoke(messages),
                        timeout=timeout,
                    )
                else:
                    response = await asyncio.wait_for(
                        llm.ainvoke(messages),
                        timeout=timeout,
                    )

                elapsed_ms = int((time.time() - start_time) * 1000)
                logger.info(
                    "agent_invoke_end",
                    agent=self.name,
                    provider=provider_name,
                    latency_ms=elapsed_ms,
                    has_tool_calls=bool(response.tool_calls),
                )

                self._record_token_usage(response, elapsed_ms)
                return response

            except TimeoutError:
                elapsed_ms = int((time.time() - start_time) * 1000)
                logger.error(
                    "agent_invoke_timeout",
                    agent=self.name,
                    provider=provider_name if attempt == 0 else "deepseek",
                    timeout_seconds=timeout,
                    latency_ms=elapsed_ms,
                )
                if attempt == 1:  # 第二次也超时
                    raise TimeoutError(f"Agent {self.name} invoke timeout after {timeout}s")

            except Exception as e:
                elapsed_ms = int((time.time() - start_time) * 1000)
                error_str = str(e).lower()
                logger.warning(
                    "agent_invoke_error",
                    agent=self.name,
                    provider=provider_name if attempt == 0 else "deepseek",
                    error=str(e),
                    attempt=attempt + 1,
                )

                # 检查是否需要切换到DeepSeek
                if attempt == 0 and ("quota" in error_str or "limit" in error_str or "rate" in error_str or "401" in error_str):
                    logger.warning("minimax_failed_switching_to_deepseek", reason=str(e))
                    continue  # 尝试DeepSeek
                elif attempt == 1:  # DeepSeek也失败
                    raise

        raise Exception(f"Agent {self.name} failed after all attempts")

    async def _invoke_and_execute_tools(
        self,
        messages: list[BaseMessage],
        tools: list[BaseTool] | None = None,
        max_iterations: int | None = None,
        timeout: float | None = None,
    ) -> tuple[AIMessage, list[str]]:
        """调用 LLM 并执行工具调用（ReAct 风格）

        Returns:
            tuple: (最终响应, 所有调用过的工具名称列表)
        """
        tools = tools or self.get_tools()
        max_iterations = max_iterations or self._settings.agent_max_iterations
        timeout = timeout or self._settings.agent_timeout_seconds
        tool_map = {t.name: t for t in tools}

        current_messages = list(messages)
        last_response = None
        all_tools_called = []

        for i in range(max_iterations):
            try:
                response = await self._invoke_with_tools(current_messages, tools, timeout=timeout)
            except TimeoutError:
                logger.error("agent_react_timeout", agent=self.name, iteration=i)
                if last_response:
                    return last_response, all_tools_called
                raise

            last_response = response

            if not response.tool_calls:
                return response, all_tools_called

            tool_results = []
            for tc in response.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                tool_id = tc["id"]

                if tool_name not in all_tools_called:
                    all_tools_called.append(tool_name)

                logger.info(
                    "tool_call",
                    agent=self.name,
                    tool=tool_name,
                    args=tool_args,
                )

                tool = tool_map.get(tool_name)
                if tool:
                    try:
                        result = await asyncio.wait_for(
                            tool.ainvoke(tool_args),
                            timeout=timeout,
                        )
                        tool_results.append(
                            ToolMessage(
                                content=str(result),
                                tool_call_id=tool_id,
                            )
                        )
                    except TimeoutError:
                        tool_results.append(
                            ToolMessage(
                                content=f"工具执行超时: {tool_name}",
                                tool_call_id=tool_id,
                            )
                        )
                    except Exception as e:
                        tool_results.append(
                            ToolMessage(
                                content=f"工具执行失败: {str(e)}",
                                tool_call_id=tool_id,
                            )
                        )
                else:
                    tool_results.append(
                        ToolMessage(
                            content=f"未知工具: {tool_name}",
                            tool_call_id=tool_id,
                        )
                    )

            current_messages.append(response)
            current_messages.extend(tool_results)

        return last_response, all_tools_called

    def _record_token_usage(self, response: AIMessage, latency_ms: int) -> None:
        """Record token usage from LLM response"""
        try:
            usage = response.usage
            if usage:
                model = self._model_name or self._settings.default_model
                prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
                completion_tokens = getattr(usage, "completion_tokens", 0) or 0
                total_tokens = getattr(usage, "total_tokens", 0) or (prompt_tokens + completion_tokens)
                cost = estimate_cost(model, prompt_tokens, completion_tokens)

                token_usage = TokenUsage(
                    model=model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    cost=cost,
                    latency_ms=latency_ms,
                )
                counter = get_token_counter()
                counter.record(token_usage)

                logger.debug(
                    "token_usage_recorded",
                    model=model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    cost=cost,
                )
        except Exception as e:
            logger.warning("token_usage_record_failed", error=str(e))
