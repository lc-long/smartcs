from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

import structlog
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from backend.app.agents.base import BaseAgent

logger = structlog.get_logger()


@dataclass
class AgentMessage:
    """Agent间通信的消息格式"""
    sender: str
    receiver: str
    content: str
    task_id: str | None = None
    context: dict = field(default_factory=dict)


@dataclass
class AgentResponse:
    """Agent执行结果"""
    agent_name: str
    success: bool
    content: str
    tools_used: list[str] = field(default_factory=list)
    sub_results: dict[str, str] = field(default_factory=dict)


class AgentCommunicator:
    """Agent通信协调器"""

    def __init__(self):
        self._agents: dict[str, BaseAgent] = {}
        self._message_queue: asyncio.Queue[AgentMessage] = asyncio.Queue()
        self._response_cache: dict[str, AgentResponse] = {}

    def register_agent(self, name: str, agent: BaseAgent) -> None:
        self._agents[name] = agent
        logger.info("agent_registered", agent=name)

    def get_agent(self, name: str) -> BaseAgent | None:
        return self._agents.get(name)

    async def send_message(self, message: AgentMessage, **kwargs) -> AgentResponse:
        """发送消息给指定Agent并等待响应

        Args:
            message: AgentMessage instance
            **kwargs: Additional arguments passed to agent.run() (e.g., customer_id)
        """
        agent = self._agents.get(message.receiver)
        if not agent:
            return AgentResponse(
                agent_name=message.receiver,
                success=False,
                content=f"Agent {message.receiver} not found",
            )

        try:
            # 构建消息，包含上下文
            messages = []
            if message.context:
                context_str = "\n".join(f"{k}: {v}" for k, v in message.context.items())
                messages.append(SystemMessage(content=f"上下文信息：\n{context_str}"))

            messages.append(HumanMessage(content=message.content))

            # 调用Agent，传递额外参数
            response = await agent.run(messages, **kwargs)
            content = response.content if isinstance(response.content, str) else str(response.content)

            result = AgentResponse(
                agent_name=message.receiver,
                success=True,
                content=content,
                tools_used=[tc["name"] for tc in response.tool_calls] if hasattr(response, "tool_calls") and response.tool_calls else [],
            )

            # 缓存结果
            if message.task_id:
                self._response_cache[message.task_id] = result

            return result

        except Exception as e:
            logger.exception("agent_call_failed", agent=message.receiver, error=str(e))
            return AgentResponse(
                agent_name=message.receiver,
                success=False,
                content=f"Agent执行失败: {str(e)}",
            )

    async def broadcast(
        self,
        sender: str,
        receivers: list[str],
        content: str,
        context: dict | None = None,
    ) -> dict[str, AgentResponse]:
        """并行广播消息给多个Agent"""
        tasks = []
        for receiver in receivers:
            msg = AgentMessage(
                sender=sender,
                receiver=receiver,
                content=content,
                context=context or {},
            )
            tasks.append(self.send_message(msg))

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        results = {}
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                results[receivers[i]] = AgentResponse(
                    agent_name=receivers[i],
                    success=False,
                    content=str(response),
                )
            else:
                results[receivers[i]] = response

        return results

    async def sequential_call(
        self,
        sender: str,
        chain: list[tuple[str, str]],  # [(agent_name, task_description), ...]
        initial_context: dict | None = None,
    ) -> dict[str, AgentResponse]:
        """串行调用Agent链，前一个的结果作为后一个的上下文"""
        results = {}
        context = initial_context or {}

        for agent_name, task_desc in chain:
            msg = AgentMessage(
                sender=sender,
                receiver=agent_name,
                content=task_desc,
                context=context,
            )

            response = await self.send_message(msg)
            results[agent_name] = response

            # 将结果添加到上下文
            if response.success:
                context[agent_name] = response.content

        return results

    def get_cached_response(self, task_id: str) -> AgentResponse | None:
        return self._response_cache.get(task_id)

    def clear_cache(self) -> None:
        self._response_cache.clear()


_communicator: AgentCommunicator | None = None


def get_communicator() -> AgentCommunicator:
    global _communicator
    if _communicator is None:
        _communicator = AgentCommunicator()
    return _communicator
