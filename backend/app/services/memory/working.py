from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import structlog
from langchain_core.messages import BaseMessage

logger = structlog.get_logger()


@dataclass
class MemoryEntry:
    """单条记忆条目"""
    id: str
    type: str  # "observation", "thought", "action", "result"
    content: str
    agent: str | None = None
    tool: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


@dataclass
class WorkingMemory:
    """工作记忆 - 存储当前任务的推理过程和中间状态"""
    conversation_id: str
    customer_id: str
    original_request: str
    entries: list[MemoryEntry] = field(default_factory=list)
    current_plan: dict | None = None
    agent_results: dict[str, str] = field(default_factory=dict)
    is_complete: bool = False
    final_response: str | None = None

    def add_entry(self, entry_type: str, content: str, **kwargs) -> MemoryEntry:
        """添加一条记忆"""
        entry = MemoryEntry(
            id=f"{self.conversation_id}_{len(self.entries)}",
            type=entry_type,
            content=content,
            **kwargs,
        )
        self.entries.append(entry)
        logger.info(
            "memory_entry_added",
            conversation_id=self.conversation_id,
            type=entry_type,
            agent=kwargs.get("agent"),
        )
        return entry

    def add_observation(self, content: str, agent: str | None = None) -> MemoryEntry:
        """添加观察结果"""
        return self.add_entry("observation", content, agent=agent)

    def add_thought(self, content: str, agent: str | None = None) -> MemoryEntry:
        """添加思考过程"""
        return self.add_entry("thought", content, agent=agent)

    def add_action(self, content: str, tool: str, agent: str | None = None) -> MemoryEntry:
        """添加工具调用"""
        return self.add_entry("action", content, tool=tool, agent=agent)

    def add_result(self, content: str, agent: str) -> MemoryEntry:
        """添加Agent执行结果"""
        self.agent_results[agent] = content
        return self.add_entry("result", content, agent=agent)

    def get_context(self, max_entries: int = 20) -> str:
        """获取当前上下文，用于注入到LLM提示中"""
        recent_entries = self.entries[-max_entries:]
        context_parts = []

        for entry in recent_entries:
            prefix = f"[{entry.type.upper()}]"
            if entry.agent:
                prefix += f" ({entry.agent})"
            if entry.tool:
                prefix += f" [工具: {entry.tool}]"
            context_parts.append(f"{prefix}: {entry.content}")

        return "\n".join(context_parts)

    def get_agent_results(self) -> dict[str, str]:
        """获取所有Agent的结果"""
        return self.agent_results.copy()

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "conversation_id": self.conversation_id,
            "customer_id": self.customer_id,
            "original_request": self.original_request,
            "entries": [
                {
                    "id": e.id,
                    "type": e.type,
                    "content": e.content,
                    "agent": e.agent,
                    "tool": e.tool,
                    "timestamp": e.timestamp.isoformat(),
                }
                for e in self.entries
            ],
            "current_plan": self.current_plan,
            "agent_results": self.agent_results,
            "is_complete": self.is_complete,
            "final_response": self.final_response,
        }

    @classmethod
    def from_dict(cls, data: dict) -> WorkingMemory:
        """从字典反序列化"""
        memory = cls(
            conversation_id=data["conversation_id"],
            customer_id=data["customer_id"],
            original_request=data["original_request"],
        )
        for entry_data in data.get("entries", []):
            memory.entries.append(MemoryEntry(
                id=entry_data["id"],
                type=entry_data["type"],
                content=entry_data["content"],
                agent=entry_data.get("agent"),
                tool=entry_data.get("tool"),
                timestamp=datetime.fromisoformat(entry_data["timestamp"]),
            ))
        memory.current_plan = data.get("current_plan")
        memory.agent_results = data.get("agent_results", {})
        memory.is_complete = data.get("is_complete", False)
        memory.final_response = data.get("final_response")
        return memory


class WorkingMemoryStore:
    """工作记忆存储"""

    def __init__(self):
        self._memories: dict[str, WorkingMemory] = {}

    def create(
        self,
        conversation_id: str,
        customer_id: str,
        original_request: str,
    ) -> WorkingMemory:
        """创建新的工作记忆"""
        memory = WorkingMemory(
            conversation_id=conversation_id,
            customer_id=customer_id,
            original_request=original_request,
        )
        self._memories[conversation_id] = memory
        return memory

    def get(self, conversation_id: str) -> WorkingMemory | None:
        """获取工作记忆"""
        return self._memories.get(conversation_id)

    def update(self, conversation_id: str, memory: WorkingMemory) -> None:
        """更新工作记忆"""
        self._memories[conversation_id] = memory

    def delete(self, conversation_id: str) -> None:
        """删除工作记忆"""
        self._memories.pop(conversation_id, None)

    def list_all(self) -> list[str]:
        """列出所有会话ID"""
        return list(self._memories.keys())


_store: WorkingMemoryStore | None = None


def get_working_memory_store() -> WorkingMemoryStore:
    global _store
    if _store is None:
        _store = WorkingMemoryStore()
    return _store
