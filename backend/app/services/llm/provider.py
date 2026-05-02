from __future__ import annotations

import asyncio
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import structlog
from langchain_core.language_models import BaseChatModel

from backend.app.core.config.settings import Settings, get_settings

logger = structlog.get_logger()


@dataclass
class TokenUsage:
    """Token usage record"""
    timestamp: datetime = field(default_factory=datetime.now)
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    latency_ms: int = 0


@dataclass
class ModelStats:
    """Aggregate stats per model"""
    total_requests: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    total_latency_ms: int = 0


class TokenCounter:
    """Token usage counter with aggregation"""

    PRICING = {
        "MiniMax-Text-01": {"prompt": 0.001, "completion": 0.003},
        "MiniMax-M2.7": {"prompt": 0.001, "completion": 0.003},
        "gpt-4o": {"prompt": 0.005, "completion": 0.015},
        "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
        "claude-3-5-sonnet": {"prompt": 0.003, "completion": 0.015},
        "claude-3-5-haiku": {"prompt": 0.0008, "completion": 0.004},
        "deepseek-chat": {"prompt": 0.00014, "completion": 0.00028},
        "deepseek-coder": {"prompt": 0.00014, "completion": 0.00028},
    }

    def __init__(self, max_history: int = 1000):
        self._usage_history: list[TokenUsage] = []
        self._model_stats: dict[str, ModelStats] = {}
        self._lock = threading.Lock()
        self._max_history = max_history

    def record(self, usage: TokenUsage) -> None:
        with self._lock:
            self._usage_history.append(usage)
            if len(self._usage_history) > self._max_history:
                self._usage_history = self._usage_history[-self._max_history:]

            model = usage.model
            if model not in self._model_stats:
                self._model_stats[model] = ModelStats()
            stats = self._model_stats[model]
            stats.total_requests += 1
            stats.total_prompt_tokens += usage.prompt_tokens
            stats.total_completion_tokens += usage.completion_tokens
            stats.total_tokens += usage.total_tokens
            stats.total_cost += usage.cost
            stats.total_latency_ms += usage.latency_ms

    def get_usage(self, model: str | None = None) -> list[TokenUsage] | dict[str, ModelStats]:
        with self._lock:
            if model:
                return [u for u in self._usage_history if u.model == model]
            return {k: v for k, v in self._model_stats.items()}

    def get_stats(self, model: str) -> ModelStats | None:
        with self._lock:
            return self._model_stats.get(model)

    def get_total_stats(self) -> dict[str, Any]:
        with self._lock:
            total = {
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
            }
            for stats in self._model_stats.values():
                total["total_requests"] += stats.total_requests
                total["total_tokens"] += stats.total_tokens
                total["total_cost"] += stats.total_cost
            return total


_token_counter: TokenCounter | None = None


def get_token_counter() -> TokenCounter:
    global _token_counter
    if _token_counter is None:
        _token_counter = TokenCounter()
    return _token_counter


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = TokenCounter.PRICING.get(model, {"prompt": 0.001, "completion": 0.003})
    return prompt_tokens * pricing["prompt"] + completion_tokens * pricing["completion"]


class LLMProvider:
    def __init__(self, settings: Settings | None = None):
        self._settings = settings or get_settings()
        self._cache: dict[str, BaseChatModel] = {}
        self._token_counter = get_token_counter()

    def get_llm(
        self,
        model_name: str | None = None,
        temperature: float = 0.3,
    ) -> BaseChatModel:
        model_name = model_name or self._settings.default_model
        cache_key = f"{model_name}:{temperature}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        llm = self._create_llm(model_name, temperature)
        self._cache[cache_key] = llm
        return llm

    async def invoke_with_retry(
        self,
        llm: BaseChatModel,
        messages: list,
        timeout: float | None = None,
    ) -> Any:
        """Invoke LLM with retry and exponential backoff."""
        settings = self._settings
        max_retries = settings.agent_retry_attempts
        base_delay = settings.agent_retry_delay
        timeout = timeout or settings.agent_timeout_seconds
        last_error: Exception | None = None

        for attempt in range(max_retries):
            try:
                return await asyncio.wait_for(llm.ainvoke(messages), timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning(
                    "llm_invoke_timeout",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    timeout=timeout,
                )
                raise
            except Exception as e:
                last_error = e
                logger.warning(
                    "llm_invoke_error",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    error=str(e),
                )
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)

        logger.error("llm_invoke_all_retries_failed", error=str(last_error))
        raise last_error

    def _create_llm(self, model_name: str, temperature: float) -> BaseChatModel:
        provider = self._settings.llm_provider

        if provider == "minimax":
            return self._create_minimax_llm(model_name, temperature)
        elif provider == "deepseek" or model_name.startswith("deepseek"):
            return self._create_deepseek_llm(model_name, temperature)
        elif provider == "anthropic" or model_name.startswith("claude"):
            return self._create_anthropic_llm(model_name, temperature)
        else:
            return self._create_openai_llm(model_name, temperature)

    def _create_minimax_llm(self, model_name: str, temperature: float) -> BaseChatModel:
        from langchain_openai import ChatOpenAI

        logger.info("creating_minimax_llm", model=model_name, temperature=temperature)
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=self._settings.minimax_api_key,
            base_url=self._settings.minimax_base_url,
        )

    def _create_deepseek_llm(self, model_name: str, temperature: float) -> BaseChatModel:
        from langchain_openai import ChatOpenAI

        logger.info("creating_deepseek_llm", model=model_name, temperature=temperature)
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=self._settings.deepseek_api_key,
            base_url=self._settings.deepseek_base_url,
        )

    def _create_openai_llm(self, model_name: str, temperature: float) -> BaseChatModel:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=self._settings.openai_api_key,
            base_url=self._settings.openai_base_url,
        )

    def _create_anthropic_llm(self, model_name: str, temperature: float) -> BaseChatModel:
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model_name=model_name,
            temperature=temperature,
            api_key=self._settings.anthropic_api_key,
        )

    def get_model_for_agent(self, agent_name: str) -> str:
        agent_model_map = {
            "router": self._settings.router_model,
            "billing": self._settings.billing_model,
            "technical": self._settings.technical_model,
            "refund": self._settings.refund_model,
            "general": self._settings.general_model,
        }
        return agent_model_map.get(agent_name, self._settings.default_model)


_llm_provider: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = LLMProvider()
    return _llm_provider