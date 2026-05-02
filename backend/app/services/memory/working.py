from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import structlog
from langchain_core.messages import BaseMessage

logger = structlog.get_logger()


@dataclass
class MemoryEntry:
    """单条记忆条目"""
    id: str
    type: str
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
    last_accessed: datetime = field(default_factory=datetime.now)

    def touch(self) -> None:
        """更新最后访问时间"""
        self.last_accessed = datetime.now()

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
            "last_accessed": self.last_accessed.isoformat(),
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
        memory.last_accessed = datetime.fromisoformat(data.get("last_accessed", datetime.now().isoformat()))
        return memory


class WorkingMemoryStore:
    """工作记忆存储 - 支持LRU清理和TTL过期"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self._memories: dict[str, WorkingMemory] = {}
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self._cleanup_thread: threading.Thread | None = None

    def _start_cleanup_thread(self) -> None:
        """启动后台清理线程"""
        if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
            self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            self._cleanup_thread.start()

    def _cleanup_loop(self) -> None:
        """定期清理过期记忆"""
        while True:
            import time
            time.sleep(60)
            self._cleanup_expired()

    def _cleanup_expired(self) -> None:
        """清理过期记忆"""
        with self._lock:
            now = datetime.now()
            expired_keys = []
            for key, memory in self._memories.items():
                if (now - memory.last_accessed).total_seconds() > self._ttl_seconds:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._memories[key]
                logger.info("memory_expired", conversation_id=key)

            if expired_keys:
                logger.info("memory_cleanup", removed_count=len(expired_keys), remaining=len(self._memories))

    def _evict_if_needed(self) -> None:
        """如果超过最大容量，LRU淘汰"""
        if len(self._memories) >= self._max_size:
            oldest_key = None
            oldest_time = datetime.max
            for key, memory in self._memories.items():
                if memory.last_accessed < oldest_time:
                    oldest_time = memory.last_accessed
                    oldest_key = key

            if oldest_key:
                del self._memories[oldest_key]
                logger.info("memory_evicted", conversation_id=oldest_key)

    def create(
        self,
        conversation_id: str,
        customer_id: str,
        original_request: str,
    ) -> WorkingMemory:
        """创建新的工作记忆"""
        with self._lock:
            self._evict_if_needed()
            memory = WorkingMemory(
                conversation_id=conversation_id,
                customer_id=customer_id,
                original_request=original_request,
            )
            self._memories[conversation_id] = memory
            self._start_cleanup_thread()
            return memory

    def get(self, conversation_id: str) -> WorkingMemory | None:
        """获取工作记忆"""
        memory = self._memories.get(conversation_id)
        if memory:
            memory.touch()
        return memory

    def update(self, conversation_id: str, memory: WorkingMemory) -> None:
        """更新工作记忆"""
        with self._lock:
            memory.touch()
            self._memories[conversation_id] = memory

    def delete(self, conversation_id: str) -> None:
        """删除工作记忆"""
        with self._lock:
            self._memories.pop(conversation_id, None)

    def list_all(self) -> list[str]:
        """列出所有会话ID"""
        return list(self._memories.keys())

    @property
    def size(self) -> int:
        """当前存储的记忆数量"""
        return len(self._memories)


_store: WorkingMemoryStore | None = None


def get_working_memory_store() -> WorkingMemoryStore:
    global _store
    if _store is None:
        from backend.app.core.config.settings import get_settings
        settings = get_settings()
        _store = WorkingMemoryStore(
            max_size=settings.working_memory_max_size,
            ttl_seconds=settings.working_memory_ttl_seconds,
        )
    return _store