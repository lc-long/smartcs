from __future__ import annotations

import pytest
from backend.app.services.llm.provider import LLMProvider, get_llm_provider


class TestLLMProvider:
    def test_singleton(self):
        p1 = get_llm_provider()
        p2 = get_llm_provider()
        assert p1 is p2

    def test_model_for_agent_mapping(self):
        provider = LLMProvider()
        assert provider.get_model_for_agent("router") == provider._settings.router_model
        assert provider.get_model_for_agent("billing") == provider._settings.billing_model
        assert provider.get_model_for_agent("unknown") == provider._settings.default_model

    def test_custom_settings(self):
        from backend.app.core.config.settings import Settings
        settings = Settings(default_model="gpt-4o", router_model="gpt-4o-mini")
        provider = LLMProvider(settings=settings)
        assert provider.get_model_for_agent("router") == "gpt-4o-mini"
        assert provider._settings.default_model == "gpt-4o"
