from __future__ import annotations

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage

from backend.app.core.config.settings import Settings, get_settings

logger = structlog.get_logger()


class LLMProvider:
    def __init__(self, settings: Settings | None = None):
        self._settings = settings or get_settings()
        self._cache: dict[str, BaseChatModel] = {}

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

    def _create_llm(self, model_name: str, temperature: float) -> BaseChatModel:
        if model_name.startswith("gpt") or model_name.startswith("o1"):
            return self._create_openai_llm(model_name, temperature)
        elif model_name.startswith("claude"):
            return self._create_anthropic_llm(model_name, temperature)
        else:
            return self._create_openai_llm(model_name, temperature)

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
