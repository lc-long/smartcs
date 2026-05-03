from __future__ import annotations

import asyncio
import structlog
from dataclasses import dataclass
from enum import Enum
from typing import Any

import structlog

from backend.app.core.config.settings import get_settings

logger = structlog.get_logger()


class ProviderStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass
class ProviderConfig:
    name: str
    provider_type: str
    model: str
    api_key: str
    base_url: str
    timeout: float = 30.0
    max_retries: int = 2


class MultiProviderStrategy:
    def __init__(self):
        settings = get_settings()
        self._primary = ProviderConfig(
            name="minimax",
            provider_type="minimax",
            model=settings.router_model or settings.default_model,
            api_key=settings.minimax_api_key,
            base_url=settings.minimax_base_url,
        )
        self._fallback = ProviderConfig(
            name="deepseek",
            provider_type="deepseek",
            model="deepseek-chat",
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
        self._primary_status = ProviderStatus.HEALTHY
        self._fallback_status = ProviderStatus.HEALTHY

    def get_current_provider(self) -> ProviderConfig:
        if self._primary_status == ProviderStatus.HEALTHY:
            return self._primary
        if self._fallback_status == ProviderStatus.HEALTHY:
            return self._fallback
        return self._primary

    async def invoke_with_fallback(
        self,
        messages: list,
        primary_llm: Any,
        fallback_llm: Any | None = None,
    ) -> Any:
        last_error = None

        for attempt in range(2):
            try:
                if attempt == 0:
                    llm = primary_llm
                    provider_name = "minimax"
                else:
                    llm = fallback_llm or primary_llm
                    provider_name = "deepseek"

                logger.info("llm_invoking", provider=provider_name, attempt=attempt + 1)
                response = await asyncio.wait_for(
                    llm.ainvoke(messages),
                    timeout=30.0,
                )
                logger.info("llm_invoke_success", provider=provider_name)
                return response

            except asyncio.TimeoutError as e:
                last_error = e
                logger.warning(
                    "llm_invoke_timeout",
                    provider=provider_name,
                    attempt=attempt + 1,
                )
                if attempt == 0:
                    self._primary_status = ProviderStatus.DEGRADED
                    logger.warning("switching_to_fallback", reason="primary_timeout")

            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                logger.warning(
                    "llm_invoke_error",
                    provider=provider_name,
                    attempt=attempt + 1,
                    error=str(e),
                )

                if attempt == 0:
                    if "quota" in error_str or "limit" in error_str or "rate" in error_str:
                        self._primary_status = ProviderStatus.UNAVAILABLE
                        logger.warning("primary_quota_exceeded", error=str(e))
                    elif "invalid" in error_str or "unauthorized" in error_str or "401" in error_str:
                        self._primary_status = ProviderStatus.UNAVAILABLE
                        logger.error("primary_auth_failed", error=str(e))
                    else:
                        self._primary_status = ProviderStatus.DEGRADED

        logger.error("all_providers_failed", error=str(last_error))
        raise last_error

    def get_status(self) -> dict:
        return {
            "primary": {
                "name": "minimax",
                "status": self._primary_status.value,
            },
            "fallback": {
                "name": "deepseek",
                "status": self._fallback_status.value,
            },
        }

    def reset_status(self) -> None:
        self._primary_status = ProviderStatus.HEALTHY
        self._fallback_status = ProviderStatus.HEALTHY
        logger.info("provider_status_reset")


_strategy: MultiProviderStrategy | None = None


def get_provider_strategy() -> MultiProviderStrategy:
    global _strategy
    if _strategy is None:
        _strategy = MultiProviderStrategy()
    return _strategy
