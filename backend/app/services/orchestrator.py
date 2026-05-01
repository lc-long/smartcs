from __future__ import annotations

import time
from uuid import uuid4

import structlog
from langchain_core.messages import AIMessage, HumanMessage

from backend.app.services.memory.short_term import get_short_term_memory
from backend.app.workflows.customer_service import get_workflow

logger = structlog.get_logger()


async def run_chat(
    message: str,
    customer_id: str,
    conversation_id: str | None = None,
) -> dict:
    conversation_id = conversation_id or uuid4().hex
    memory = get_short_term_memory()

    await memory.add_message(conversation_id, HumanMessage(content=message))

    history = await memory.get_messages(conversation_id)
    from langchain_core.messages import HumanMessage as HM
    messages = [HM(content=entry["content"]) for entry in history]

    workflow = get_workflow()
    start = time.time()
    result = await workflow.run(
        messages=messages,
        conversation_id=conversation_id,
        customer_id=customer_id,
    )
    elapsed_ms = int((time.time() - start) * 1000)

    await memory.add_message(
        conversation_id,
        AIMessage(content=result["agent_response"]),
        agent_name=result["active_agent"],
    )

    return {
        "conversation_id": conversation_id,
        "response": result["agent_response"],
        "agent": result["active_agent"],
        "intent": result["current_intent"],
        "confidence": result["routing_confidence"],
        "needs_human": result["needs_human"],
        "latency_ms": elapsed_ms,
    }
