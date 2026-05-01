from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

import structlog
from fastapi import WebSocket, WebSocketDisconnect
from langchain_core.messages import AIMessage, HumanMessage

from backend.app.services.memory.short_term import get_short_term_memory
from backend.app.workflows.customer_service import get_workflow

logger = structlog.get_logger()


class ConnectionManager:
    def __init__(self):
        self._active: dict[str, WebSocket] = {}
        self._conversation_map: dict[str, str] = {}

    async def connect(self, websocket: WebSocket, conversation_id: str) -> None:
        await websocket.accept()
        self._active[conversation_id] = websocket
        logger.info("ws_connect", conversation_id=conversation_id)

    def disconnect(self, conversation_id: str) -> None:
        self._active.pop(conversation_id, None)
        logger.info("ws_disconnect", conversation_id=conversation_id)

    def get_connection(self, conversation_id: str) -> WebSocket | None:
        return self._active.get(conversation_id)

    async def send_event(self, conversation_id: str, event: dict[str, Any]) -> None:
        ws = self._active.get(conversation_id)
        if ws:
            try:
                await ws.send_text(json.dumps(event, ensure_ascii=False))
            except Exception:
                logger.exception("ws_send_error", conversation_id=conversation_id)

    async def broadcast_to_conversation(self, conversation_id: str, event: dict[str, Any]) -> None:
        await self.send_event(conversation_id, event)

    @property
    def active_count(self) -> int:
        return len(self._active)


manager = ConnectionManager()


async def handle_websocket(
    websocket: WebSocket,
    conversation_id: str,
    customer_id: str,
) -> None:
    await manager.connect(websocket, conversation_id)
    memory = get_short_term_memory()

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            if data.get("type") != "message":
                continue

            content = data.get("content", "").strip()
            if not content:
                continue

            await manager.send_event(conversation_id, {
                "type": "user_message",
                "content": content,
            })

            await manager.send_event(conversation_id, {
                "type": "agent_start",
                "agent": "router",
            })

            await memory.add_message(conversation_id, HumanMessage(content=content))
            history = await memory.get_messages(conversation_id)
            messages = [HumanMessage(content=entry["content"]) for entry in history]

            workflow = get_workflow()

            async def emit_callback(event_type: str, data: dict) -> None:
                await manager.send_event(conversation_id, {
                    "type": event_type,
                    **data,
                })

            result = await _run_workflow_with_events(
                workflow, messages, conversation_id, customer_id, emit_callback
            )

            await memory.add_message(
                conversation_id,
                AIMessage(content=result["agent_response"]),
                agent_name=result["active_agent"],
            )

            await manager.send_event(conversation_id, {
                "type": "agent_response",
                "content": result["agent_response"],
                "agent": result["active_agent"],
                "intent": result["current_intent"],
                "confidence": result["routing_confidence"],
                "needs_human": result["needs_human"],
            })

            await manager.send_event(conversation_id, {"type": "done"})

    except WebSocketDisconnect:
        manager.disconnect(conversation_id)
    except Exception:
        logger.exception("ws_handler_error", conversation_id=conversation_id)
        await manager.send_event(conversation_id, {
            "type": "error",
            "message": "处理请求时出现错误",
        })
        manager.disconnect(conversation_id)


async def _run_workflow_with_events(
    workflow: Any,
    messages: list,
    conversation_id: str,
    customer_id: str,
    emit_callback: Any,
) -> dict:
    from backend.app.workflows.state import CustomerServiceState
    from langgraph.graph import END, START, StateGraph

    result = await workflow.run(
        messages=messages,
        conversation_id=conversation_id,
        customer_id=customer_id,
    )

    if result.get("needs_human"):
        await emit_callback("human_approval_needed", {
            "reason": result["agent_response"],
            "conversation_id": conversation_id,
        })

    return result
