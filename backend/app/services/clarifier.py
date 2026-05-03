from __future__ import annotations

import structlog
from typing import Literal

from backend.app.models.schemas import IntentType

logger = structlog.get_logger()

CLARIFICATION_THRESHOLD = 0.5
CLARIFICATION_QUESTIONS: dict[IntentType, list[str]] = {
    IntentType.BILLING: [
        "您是想查询账单、发票还是支付问题？",
        "请问是关于哪个订单的账单问题？",
    ],
    IntentType.REFUND: [
        "您是想申请退款、查询退款进度还是退货？",
        "请问您的订单号是多少？",
    ],
    IntentType.TECHNICAL: [
        "您是遇到了什么技术问题？",
        "请问是产品使用问题还是系统故障？",
    ],
    IntentType.GENERAL: [
        "请问您想了解什么？",
        "您是想查询订单、产品还是其他信息？",
    ],
}


class IntentClarifier:
    def needs_clarification(self, confidence: float, intent: str) -> bool:
        return confidence < CLARIFICATION_THRESHOLD and intent != "escalation"

    def get_clarification_question(
        self,
        intent: str,
        user_message: str,
    ) -> str:
        intent_type = IntentType(intent) if intent in [e.value for e in IntentType] else IntentType.GENERAL
        questions = CLARIFICATION_QUESTIONS.get(intent_type, CLARIFICATION_QUESTIONS[IntentType.GENERAL])

        if user_message:
            context_hint = f"\n\n根据您提到的\"{user_message[:30]}...\"，"
            return context_hint + questions[0]
        return questions[0]

    def generate_clarification_response(
        self,
        confidence: float,
        intent: str,
        reasoning: str,
        user_message: str,
    ) -> tuple[str, str]:
        question = self.get_clarification_question(intent, user_message)
        explanation = (
            f"我对您的意图理解置信度为 {confidence:.0%}，"
            f"初步判断是 {intent} 相关问题。"
            f"\n{reasoning}"
        )
        return explanation, question


_clarifier: IntentClarifier | None = None


def get_intent_clarifier() -> IntentClarifier:
    global _clarifier
    if _clarifier is None:
        _clarifier = IntentClarifier()
    return _clarifier
