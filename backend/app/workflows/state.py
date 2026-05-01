from __future__ import annotations

from typing import TypedDict

from langchain_core.messages import BaseMessage


class CustomerServiceState(TypedDict):
    conversation_id: str
    customer_id: str
    messages: list[BaseMessage]

    current_intent: str
    routing_confidence: float
    routing_reasoning: str

    active_agent: str
    agent_response: str
    tools_called: list[str]

    needs_human: bool
    human_approved: bool
    human_comment: str | None

    token_usage: dict
    trace_id: str
