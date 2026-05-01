from __future__ import annotations

import json
import re
import time
from abc import ABC, abstractmethod
from typing import Any

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
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

    def _build_tool_descriptions(self, tools: list[BaseTool]) -> str:
        """构建工具描述，用于 prompt-based 工具调用"""
        if not tools:
            return ""

        desc = "\n\n可用工具（调用格式：{\"tool\":\"工具名\",\"params\":{\"参数\":\"值\"}}）：\n"
        for tool in tools:
            desc += f"- {tool.name}: {tool.description[:50]}\n"

        return desc

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
            # 尝试使用 bind_tools（适用于支持的 LLM）
            if tools:
                try:
                    llm_with_tools = self.llm.bind_tools(tools)
                    response = await llm_with_tools.ainvoke(messages)
                    
                    # 检查是否有 tool_calls
                    if response.tool_calls:
                        elapsed_ms = int((time.time() - start_time) * 1000)
                        logger.info(
                            "agent_invoke_end",
                            agent=self.name,
                            latency_ms=elapsed_ms,
                            has_tool_calls=True,
                        )
                        return response
                except Exception as e:
                    logger.warning("bind_tools_failed", agent=self.name, error=str(e))
                    # 降级到 prompt-based 工具调用
                    pass

            # Prompt-based 工具调用
            if tools:
                return await self._invoke_with_prompt_tools(messages, tools, start_time)
            else:
                response = await self.llm.ainvoke(messages)
                elapsed_ms = int((time.time() - start_time) * 1000)
                logger.info(
                    "agent_invoke_end",
                    agent=self.name,
                    latency_ms=elapsed_ms,
                    has_tool_calls=False,
                )
                return response

        except Exception:
            logger.exception("agent_invoke_error", agent=self.name)
            raise

    async def _invoke_with_prompt_tools(
        self,
        messages: list[BaseMessage],
        tools: list[BaseTool],
        start_time: float,
    ) -> AIMessage:
        """使用 prompt 方式调用工具（兼容所有 LLM）"""
        # 构建包含工具描述的 system prompt
        tool_desc = self._build_tool_descriptions(tools)
        system_prompt = self.get_system_prompt() + tool_desc

        # 添加 system message
        prompt_messages = [SystemMessage(content=system_prompt)] + messages

        # 调用 LLM
        response = await self.llm.ainvoke(prompt_messages)
        content = response.content if isinstance(response.content, str) else str(response.content)

        # 去除 think 标签
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

        # 解析工具调用
        tool_calls = self._parse_tool_calls(content)

        if tool_calls:
            # 执行工具
            tool_results = []
            for tc in tool_calls:
                tool_name = tc["tool"]
                tool_params = tc.get("params", {})

                # 找到对应的工具
                tool = next((t for t in tools if t.name == tool_name), None)
                if tool:
                    try:
                        result = await tool.ainvoke(tool_params)
                        tool_results.append({
                            "tool": tool_name,
                            "result": result,
                        })
                    except Exception as e:
                        tool_results.append({
                            "tool": tool_name,
                            "error": str(e),
                        })

            # 构建包含工具结果的新 prompt
            tool_results_text = "\n".join(
                f"工具 {tr['tool']} 的结果：\n{tr.get('result', tr.get('error', '执行失败'))}"
                for tr in tool_results
            )

            final_prompt = [
                SystemMessage(content=system_prompt),
                *messages,
                SystemMessage(content=f"工具调用结果：\n{tool_results_text}\n\n请根据以上工具结果回复用户。"),
            ]

            # 再次调用 LLM 生成最终回复
            final_response = await self.llm.ainvoke(final_prompt)
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(
                "agent_invoke_end",
                agent=self.name,
                latency_ms=elapsed_ms,
                tools_called=[tc["tool"] for tc in tool_calls],
            )

            # 保留原始 tool_calls 信息
            final_response.tool_calls = [
                {"name": tc["tool"], "args": tc.get("params", {})}
                for tc in tool_calls
            ]
            return final_response

        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "agent_invoke_end",
            agent=self.name,
            latency_ms=elapsed_ms,
            has_tool_calls=False,
        )
        return response

    def _parse_tool_calls(self, content: str) -> list[dict]:
        """从 LLM 回复中解析工具调用"""
        tool_calls = []

        # 尝试解析 JSON 格式的工具调用
        # 匹配 {"tool": "...", "params": {...}}
        json_pattern = r'\{[^{}]*"tool"\s*:\s*"[^"]+"[^{}]*\}'
        matches = re.findall(json_pattern, content)

        for match in matches:
            try:
                data = json.loads(match)
                if "tool" in data:
                    tool_calls.append(data)
            except json.JSONDecodeError:
                continue

        # 如果没找到，尝试解析更宽松的格式
        if not tool_calls:
            # 匹配 tool: xxx 或 tool_name: xxx
            simple_pattern = r'(?:tool|tool_name)\s*[=:]\s*["\']?(\w+)["\']?'
            matches = re.findall(simple_pattern, content)
            for tool_name in matches:
                tool_calls.append({"tool": tool_name, "params": {}})

        return tool_calls
