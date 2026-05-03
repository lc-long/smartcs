from __future__ import annotations

import asyncio
import json
from typing import Any

import structlog
from fastapi import WebSocket, WebSocketDisconnect

logger = structlog.get_logger()


class AdminConnectionManager:
    def __init__(self):
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, admin_id: str) -> None:
        await websocket.accept()
        self._connections[admin_id] = websocket
        logger.info("admin_ws_connect", admin_id=admin_id)

    def disconnect(self, admin_id: str) -> None:
        self._connections.pop(admin_id, None)
        logger.info("admin_ws_disconnect", admin_id=admin_id)

    async def send_event(self, admin_id: str, event: dict[str, Any]) -> None:
        ws = self._connections.get(admin_id)
        if ws:
            try:
                await ws.send_text(json.dumps(event, ensure_ascii=False))
            except Exception:
                logger.exception("admin_ws_send_error", admin_id=admin_id)

    async def broadcast_to_all(self, event: dict[str, Any]) -> None:
        disconnected = []
        for admin_id, ws in self._connections.items():
            try:
                await ws.send_text(json.dumps(event, ensure_ascii=False))
            except Exception:
                disconnected.append(admin_id)

        for admin_id in disconnected:
            self._connections.pop(admin_id, None)

    async def broadcast_approval_update(self, approval_id: str, decision: str, item: dict) -> None:
        await self.broadcast_to_all({
            "type": "approval_update",
            "approval_id": approval_id,
            "decision": decision,
            "item": item,
        })

    @property
    def active_count(self) -> int:
        return len(self._connections)


admin_manager = AdminConnectionManager()
