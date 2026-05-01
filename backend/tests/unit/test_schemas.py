from __future__ import annotations

import pytest
from backend.app.models.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatResponseMetadata,
    IntentType,
    MessageRole,
    RouteDecision,
)


class TestIntentType:
    def test_intent_values(self):
        assert IntentType.BILLING.value == "billing"
        assert IntentType.TECHNICAL.value == "technical"
        assert IntentType.REFUND.value == "refund"
        assert IntentType.GENERAL.value == "general"
        assert IntentType.ESCALATION.value == "escalation"


class TestRouteDecision:
    def test_valid_decision(self):
        decision = RouteDecision(
            intent=IntentType.BILLING,
            confidence=0.95,
            reasoning="用户提到账单",
            suggested_agent="billing",
        )
        assert decision.intent == IntentType.BILLING
        assert decision.confidence == 0.95

    def test_confidence_bounds(self):
        with pytest.raises(Exception):
            RouteDecision(
                intent=IntentType.BILLING,
                confidence=1.5,
                reasoning="test",
                suggested_agent="billing",
            )


class TestChatRequest:
    def test_valid_request(self):
        req = ChatRequest(
            customer_id="C001",
            message="我想查账单",
        )
        assert req.customer_id == "C001"
        assert req.stream is False

    def test_empty_message_rejected(self):
        with pytest.raises(Exception):
            ChatRequest(customer_id="C001", message="")

    def test_with_conversation_id(self):
        from uuid import uuid4
        cid = uuid4()
        req = ChatRequest(
            customer_id="C001",
            message="hello",
            conversation_id=cid,
        )
        assert req.conversation_id == cid


class TestChatMessage:
    def test_default_values(self):
        msg = ChatMessage(role=MessageRole.USER, content="hello")
        assert msg.role == MessageRole.USER
        assert msg.tools_called == []
        assert msg.agent_name is None
