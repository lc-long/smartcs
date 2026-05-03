from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

import structlog
from pydantic import BaseModel

logger = structlog.get_logger()


class A2AMessageType(str, Enum):
    TASK_DELEGATE = "task_delegate"
    RESULT_RETURN = "result_return"
    CAPABILITY_QUERY = "capability_query"
    CAPABILITY_RESPONSE = "capability_response"
    CONTEXT_SHARE = "context_share"
    HEARTBEAT = "heartbeat"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentCapability(BaseModel):
    name: str
    description: str
    intent_types: list[str]
    tools: list[str]
    max_concurrent_tasks: int = 5
    version: str = "1.0"


class A2AMessage(BaseModel):
    id: str = field(default_factory=lambda: str(uuid4()))
    type: A2AMessageType
    sender: str
    receiver: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    task_id: str | None = None
    reply_to: str | None = None
    payload: dict = field(default_factory=dict)

    class Config:
        use_enum_values = True


@dataclass
class A2ATask:
    id: str
    delegate_agent: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    context: dict = field(default_factory=dict)
    subtasks: list[A2ATask] = field(default_factory=list)


class CapabilityRegistry:
    def __init__(self):
        self._capabilities: dict[str, AgentCapability] = {}

    def register(self, capability: AgentCapability) -> None:
        self._capabilities[capability.name] = capability
        logger.info("agent_capability_registered", agent=capability.name)

    def get(self, name: str) -> AgentCapability | None:
        return self._capabilities.get(name)

    def get_all(self) -> list[AgentCapability]:
        return list(self._capabilities.values())

    def find_agent_for_intent(self, intent: str) -> list[AgentCapability]:
        return [
            cap for cap in self._capabilities.values()
            if intent in cap.intent_types
        ]

    def find_agent_for_tool(self, tool: str) -> list[AgentCapability]:
        return [
            cap for cap in self._capabilities.values()
            if tool in cap.tools
        ]


_capability_registry: CapabilityRegistry | None = None


def get_capability_registry() -> CapabilityRegistry:
    global _capability_registry
    if _capability_registry is None:
        _capability_registry = CapabilityRegistry()
    return _capability_registry


class A2AProtocol:
    def __init__(self):
        self._inbox: asyncio.Queue[A2AMessage] = asyncio.Queue()
        self._tasks: dict[str, A2ATask] = {}
        self._callbacks: dict[str, asyncio.Future] = {}
        self._capabilities = get_capability_registry()

    async def send(
        self,
        message_type: A2AMessageType,
        sender: str,
        receiver: str | None = None,
        task_id: str | None = None,
        payload: dict | None = None,
        wait_for_response: bool = False,
        timeout: float = 30.0,
    ) -> A2AMessage | None:
        message = A2AMessage(
            type=message_type,
            sender=sender,
            receiver=receiver,
            task_id=task_id,
            payload=payload or {},
        )

        if wait_for_response and message.id:
            future = asyncio.get_running_loop().create_future()
            self._callbacks[message.id] = future

        await self._inbox.put(message)

        if wait_for_response and message.id:
            try:
                return await asyncio.wait_for(future, timeout=timeout)
            except TimeoutError:
                logger.warning("a2a_response_timeout", message_id=message.id)
                self._callbacks.pop(message.id, None)
                return None

        return message

    async def receive(self) -> A2AMessage:
        return await self._inbox.get()

    def reply(self, original: A2AMessage, payload: dict) -> A2AMessage:
        return A2AMessage(
            type=A2AMessageType.RESULT_RETURN,
            sender=original.receiver,
            receiver=original.sender,
            reply_to=original.id,
            task_id=original.task_id,
            payload=payload,
        )

    def handle_incoming(self, message: A2AMessage) -> None:
        if message.reply_to and message.reply_to in self._callbacks:
            future = self._callbacks.pop(message.reply_to)
            if not future.done():
                future.set_result(message)

    def create_task(
        self,
        delegate_agent: str,
        description: str,
        context: dict | None = None,
    ) -> A2ATask:
        task = A2ATask(
            id=str(uuid4()),
            delegate_agent=delegate_agent,
            description=description,
            context=context or {},
        )
        self._tasks[task.id] = task
        return task

    def get_task(self, task_id: str) -> A2ATask | None:
        return self._tasks.get(task_id)

    def update_task(self, task_id: str, **kwargs) -> None:
        if task_id in self._tasks:
            task = self._tasks[task_id]
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            task.updated_at = datetime.now()

    async def delegate_task(
        self,
        agent_name: str,
        task_description: str,
        context: dict | None = None,
        wait: bool = True,
        timeout: float = 60.0,
    ) -> A2ATask | None:
        task = self.create_task(agent_name, task_description, context)

        await self.send(
            A2AMessageType.TASK_DELEGATE,
            sender="workflow",
            receiver=agent_name,
            task_id=task.id,
            payload={
                "description": task_description,
                "context": context or {},
            },
            wait_for_response=wait,
            timeout=timeout,
        )

        return task


_a2a_protocol: A2AProtocol | None = None


def get_a2a_protocol() -> A2AProtocol:
    global _a2a_protocol
    if _a2a_protocol is None:
        _a2a_protocol = A2AProtocol()
    return _a2a_protocol
