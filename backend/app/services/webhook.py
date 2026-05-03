from __future__ import annotations

import asyncio
import structlog
from typing import Any

import httpx

logger = structlog.get_logger()


class WebhookService:
    def __init__(self):
        self._urls: list[str] = []
        self._timeout = 10.0

    def register(self, url: str) -> bool:
        if not url.startswith(("http://", "https://")):
            logger.warning("invalid_webhook_url", url=url)
            return False
        self._urls.append(url)
        logger.info("webhook_registered", url=url)
        return True

    def unregister(self, url: str) -> None:
        if url in self._urls:
            self._urls.remove(url)

    async def notify(self, event_type: str, data: dict[str, Any]) -> None:
        for url in self._urls:
            asyncio.create_task(self._send(url, event_type, data))

    async def _send(self, url: str, event_type: str, data: dict[str, Any]) -> None:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    url,
                    json={"event": event_type, "data": data},
                    headers={"Content-Type": "application/json"},
                )
                logger.info("webhook_sent", url=url, event=event_type, status=response.status_code)
        except Exception as e:
            logger.warning("webhook_failed", url=url, event=event_type, error=str(e))


_webhook_service: WebhookService | None = None


def get_webhook_service() -> WebhookService:
    global _webhook_service
    if _webhook_service is None:
        _webhook_service = WebhookService()
    return _webhook_service
