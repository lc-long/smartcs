from __future__ import annotations

import json
import re

import structlog
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from backend.app.agents.base import BaseAgent
from backend.app.models.schemas import IntentType, RouteDecision
from backend.app.services.llm.provider import LLMProvider

logger = structlog.get_logger()

SYSTEM_PROMPT = """你是一个意图分类器。分析用户消息，输出JSON格式的分类结果。

意图类别：
- billing: 账单、发票、支付、扣费
- technical: 技术、故障、设备、问题、bug
- refund: 退款、退货、退钱
- escalation: 人工、转人工
- general: 其他

输出格式（仅输出JSON，不要其他内容）：
{"intent": "billing", "confidence": 0.9, "reasoning": "理由"}"""

INTENT_KEYWORDS = {
    IntentType.ESCALATION: ["人工", "转人工", "找人工", "真人", "客服"],
    IntentType.BILLING: ["账单", "发票", "扣费", "付款", "充值", "缴费", "欠费", "账单查询", "查账单"],
    IntentType.REFUND: ["退款", "退货", "退钱", "退费", "退订", "订单", "查订单", "订单查询"],
    IntentType.TECHNICAL: ["故障", "设备", "技术", "坏了", "不开机", "无法", "bug", "报错", "怎么办", "问题", "屏幕", "闪烁"],
}

INTENT_MAPPING = {
    "billing": IntentType.BILLING,
    "账单": IntentType.BILLING,
    "technical": IntentType.TECHNICAL,
    "技术": IntentType.TECHNICAL,
    "refund": IntentType.REFUND,
    "退款": IntentType.REFUND,
    "escalation": IntentType.ESCALATION,
    "人工": IntentType.ESCALATION,
    "general": IntentType.GENERAL,
    "通用": IntentType.GENERAL,
}


class RouterAgent(BaseAgent):
    name = "router"
    description = "意图分类路由Agent"

    def __init__(self, llm_provider: LLMProvider):
        super().__init__(
            llm_provider=llm_provider,
            temperature=0.0,
        )

    async def run(self, messages: list[BaseMessage], **kwargs: dict) -> AIMessage:
        raise NotImplementedError("Use classify_intent instead")

    async def classify_intent(self, messages: list[BaseMessage]) -> RouteDecision:
        logger.info("router_classify_start", message_count=len(messages))

        # 只分析最后一条用户消息
        user_text = ""
        for msg in reversed(messages):
            if hasattr(msg, "content") and isinstance(msg.content, str) and msg.content.strip():
                user_text = msg.content
                break

        logger.info("router_user_text", text=user_text[:200])

        keyword_result = self._classify_by_keywords(user_text)
        if keyword_result and keyword_result.confidence >= 0.8:
            logger.info(
                "router_keyword_match",
                intent=keyword_result.intent.value,
                confidence=keyword_result.confidence,
            )
            return keyword_result

        try:
            prompt_messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
            response: AIMessage = await self.llm.ainvoke(prompt_messages)
            content = response.content if isinstance(response.content, str) else str(response.content)
            decision = self._parse_response(content, user_text)
        except Exception as e:
            logger.warning("router_llm_failed", error=str(e))
            decision = keyword_result or RouteDecision(
                intent=IntentType.GENERAL,
                confidence=0.3,
                reasoning="分类失败，降级到通用处理",
                suggested_agent="general",
            )

        logger.info(
            "router_classify_end",
            intent=decision.intent.value,
            confidence=decision.confidence,
        )
        return decision

    def _classify_by_keywords(self, text: str) -> RouteDecision | None:
        text_lower = text.lower()
        for intent, keywords in INTENT_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    return RouteDecision(
                        intent=intent,
                        confidence=0.9,
                        reasoning=f"关键词匹配: {kw}",
                        suggested_agent=self.get_agent_for_intent(intent),
                    )
        return None

    def _parse_response(self, content: str, user_text: str = "") -> RouteDecision:
        content = content.strip()

        first_brace = content.find("{")
        last_brace = content.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            content = content[first_brace:last_brace + 1]
        elif content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])

        data = json.loads(content)
        if "reason" in data and "reasoning" not in data:
            data["reasoning"] = data.pop("reason")

        intent_raw = str(data.get("intent", "")).lower().strip()
        intent = INTENT_MAPPING.get(intent_raw)
        if intent is None:
            for key, val in INTENT_MAPPING.items():
                if key in intent_raw or intent_raw in key:
                    intent = val
                    break
        if intent is None:
            intent = IntentType.GENERAL

        return RouteDecision(
            intent=intent,
            confidence=float(data.get("confidence", 0.5)),
            reasoning=str(data.get("reasoning", "")),
            suggested_agent=self.get_agent_for_intent(intent),
        )

    def get_agent_for_intent(self, intent: IntentType) -> str:
        mapping = {
            IntentType.BILLING: "billing",
            IntentType.TECHNICAL: "technical",
            IntentType.REFUND: "refund",
            IntentType.GENERAL: "general",
            IntentType.ESCALATION: "escalation",
        }
        return mapping.get(intent, "general")
