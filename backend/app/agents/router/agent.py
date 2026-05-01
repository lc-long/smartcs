from __future__ import annotations

import structlog
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from backend.app.agents.base import BaseAgent
from backend.app.models.schemas import IntentType, RouteDecision
from backend.app.services.llm.provider import LLMProvider

logger = structlog.get_logger()

SYSTEM_PROMPT = """你是一个智能客服意图分类器。分析用户消息，判断意图类别。

意图类别（必须使用以下英文值）：
- billing: 账单相关（发票、支付历史、账单金额）
- technical: 技术支持（产品故障、使用问题）
- refund: 退款相关（退款申请、退款进度）
- escalation: 用户明确要求人工客服
- general: 其他无法分类的问题

规则：
- 用户说"人工"、"转人工"直接归为 escalation
- 无法确定时归为 general
- intent字段必须是上面的英文值之一

请直接输出JSON，不要输出其他内容：
{"intent": "billing", "confidence": 0.9, "reasoning": "理由"}"""

INTENT_MAPPING = {
    "billing": IntentType.BILLING,
    "账单": IntentType.BILLING,
    "发票": IntentType.BILLING,
    "支付": IntentType.BILLING,
    "technical": IntentType.TECHNICAL,
    "技术": IntentType.TECHNICAL,
    "故障": IntentType.TECHNICAL,
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

        prompt_messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

        response: AIMessage = await self.llm.ainvoke(prompt_messages)
        content = response.content if isinstance(response.content, str) else str(response.content)

        try:
            decision = self._parse_response(content)
        except (ValueError, KeyError):
            logger.warning("router_parse_failed", raw_content=content[:200])
            decision = RouteDecision(
                intent=IntentType.GENERAL,
                confidence=0.3,
                reasoning="无法解析分类结果，降级到通用处理",
                suggested_agent="general",
            )

        logger.info(
            "router_classify_end",
            intent=decision.intent.value,
            confidence=decision.confidence,
        )
        return decision

    def _parse_response(self, content: str) -> RouteDecision:
        import json

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
