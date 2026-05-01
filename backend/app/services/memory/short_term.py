from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


class InMemoryStore:
    def __init__(self, max_messages_per_session: int = 50):
        self._sessions: dict[str, list[dict]] = {}
        self._max_messages = max_messages_per_session

    async def add_message(self, session_id: str, message: BaseMessage, agent_name: str | None = None) -> None:
        if session_id not in self._sessions:
            self._sessions[session_id] = []

        role = "user" if isinstance(message, HumanMessage) else "assistant"
        content = message.content if isinstance(message.content, str) else str(message.content)

        self._sessions[session_id].append({
            "role": role,
            "content": content,
            "agent_name": agent_name,
        })

        if len(self._sessions[session_id]) > self._max_messages:
            self._sessions[session_id] = self._sessions[session_id][-self._max_messages:]

    async def get_messages(self, session_id: str, limit: int | None = None) -> list[dict]:
        messages = self._sessions.get(session_id, [])
        if limit:
            return messages[-limit:]
        return messages

    async def clear_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    async def get_session_ids(self) -> list[str]:
        return list(self._sessions.keys())


_short_term_store: InMemoryStore | None = None


def get_short_term_memory() -> InMemoryStore:
    global _short_term_store
    if _short_term_store is None:
        _short_term_store = InMemoryStore()
    return _short_term_store
