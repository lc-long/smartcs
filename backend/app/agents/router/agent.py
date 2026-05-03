from __future__ import annotations

import json
import re

import structlog
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from backend.app.agents.base import BaseAgent
from backend.app.models.schemas import IntentType, RouteDecision
from backend.app.services.llm.provider import LLMProvider

logger = structlog.get_logger()

MAX_ROUTER_RETRIES = 2
ROUTER_RETRY_DELAY = 0.5

SYSTEM_PROMPT = """你是一个意图分类器。分析用户消息，输出JSON格式的分类结果。

**重要：你需要分析用户当前的完整对话上下文，而不仅仅是最后一条消息。**
用户可能在之前的消息中表达了意图，然后在后续消息中补充细节或改变了话题。

意图类别：
- billing: 账单、发票、支付、扣费相关查询
- technical: 技术问题、设备故障、产品问题
- refund: 退款、退货、退钱相关操作（注意：查订单不等于退款）
- escalation: 用户明确要求人工客服
- general: 订单查询、产品咨询、其他问题

重要区分：
- "查订单"、"订单查询"、"check orders" → general（只是查询，不是退款）
- "退款"、"退货"、"申请退款"、"refund" → refund（明确要退款）
- "查账单"、"发票"、"billing" → billing
- 如果用户说"那个"或"之前那个"，需要结合对话历史判断指的是什么

单意图检测：用户只表达一个意图时输出单条结果。
多意图检测：用户同时表达多个意图时，使用"intents"数组返回多个意图。
- "我想退款，另外帮我查下账单" → ["refund", "billing"]
- "这个手表坏了，要退款，建个工单" → ["technical", "refund"]
- "查下积分，顺便推荐个产品" → ["general"]（积分查询和推荐都在general范围内）

输出格式（仅输出JSON，不要其他内容）：
单意图：{"intent": "billing", "confidence": 0.9, "reasoning": "理由"}
多意图：{"intents": ["billing", "refund"], "confidence": 0.85, "reasoning": "检测到多个意图", "is_multi": true}"""

INTENT_KEYWORDS = {
    IntentType.ESCALATION: ["转人工", "找人工", "真人客服", "人工服务", "转接人工", "transfer to human", "human agent"],
    IntentType.BILLING: ["账单", "发票", "扣费", "付款", "充值", "缴费", "欠费", "billing", "invoice", "payment"],
    IntentType.REFUND: ["退款", "退货", "退钱", "退费", "退订", "申请退款", "退款申请", "退货退款", "refund", "return"],
    IntentType.TECHNICAL: ["故障", "设备", "技术", "坏了", "不开机", "无法", "bug", "报错", "屏幕", "闪烁", "换货", "维修", "怎么办", "technical", "broken", "not working"],
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

        # 构建完整对话上下文用于分析
        user_messages = [
            m.content for m in messages
            if hasattr(m, "content") and isinstance(m.content, str)
        ]
        # 用最后3条消息作为上下文
        recent_context = "\n".join(user_messages[-3:]) if len(user_messages) > 1 else (user_messages[-1] if user_messages else "")

        # 如果只有一条消息，直接用这条
        if len(user_messages) == 1:
            user_text = user_messages[0]
        else:
            # 多条消息时，用最后一条但考虑上下文
            user_text = user_messages[-1]

        logger.info("router_user_text", text=user_text[:200], context_len=len(recent_context))

        keyword_result = self._classify_by_keywords(user_text, recent_context)
        if keyword_result and keyword_result.confidence >= 0.8:
            logger.info(
                "router_keyword_match",
                intent=keyword_result.intent.value,
                confidence=keyword_result.confidence,
            )
            return keyword_result

        decision = await self._classify_with_retry(messages, user_text, keyword_result, recent_context)

        logger.info(
            "router_classify_end",
            intent=decision.intent.value,
            confidence=decision.confidence,
        )
        return decision

    async def _classify_with_retry(
        self,
        messages: list[BaseMessage],
        user_text: str,
        keyword_result: RouteDecision | None,
        recent_context: str = "",
    ) -> RouteDecision:
        """LLM分类，带重试机制"""
        # 在系统提示中附加对话上下文
        context_note = f"\n\n对话上下文（最近消息）：\n{recent_context}" if recent_context else ""
        prompt_with_context = SYSTEM_PROMPT + context_note
        prompt_messages = [SystemMessage(content=prompt_with_context)] + messages
        last_error: Exception | None = None

        for attempt in range(MAX_ROUTER_RETRIES):
            try:
                response: AIMessage = await self.llm.ainvoke(prompt_messages)
                content = response.content if isinstance(response.content, str) else str(response.content)
                return self._parse_response(content, user_text)
            except Exception as e:
                last_error = e
                logger.warning(
                    "router_llm_retry",
                    attempt=attempt + 1,
                    max_retries=MAX_ROUTER_RETRIES,
                    error=str(e),
                )
                if attempt < MAX_ROUTER_RETRIES - 1:
                    import asyncio
                    await asyncio.sleep(ROUTER_RETRY_DELAY * (attempt + 1))

        logger.error("router_llm_all_retries_failed", error=str(last_error))
        return keyword_result or RouteDecision(
            intent=IntentType.GENERAL,
            confidence=0.3,
            reasoning="分类失败，降级到通用处理",
            suggested_agent="general",
        )

    def _classify_by_keywords(self, text: str, context: str = "") -> RouteDecision | None:
        # 优先在上下文中查找关键词
        search_text = f"{context}\n{text}".lower()
        for intent, keywords in INTENT_KEYWORDS.items():
            for kw in keywords:
                if kw in search_text:
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

        # Check for multi-intent
        if "intents" in data:
            intents = data["intents"]
            if isinstance(intents, list) and len(intents) > 1:
                primary_intent_raw = intents[0].lower().strip()
                primary_intent = self._map_intent(primary_intent_raw)
                return RouteDecision(
                    intent=primary_intent,
                    confidence=float(data.get("confidence", 0.8)),
                    reasoning=str(data.get("reasoning", f"检测到{len(intents)}个意图: {', '.join(intents)}")),
                    suggested_agent=self.get_agent_for_intent(primary_intent),
                    is_multi_intent=True,
                    all_intents=[self._map_intent(i.lower().strip()) for i in intents],
                )

        intent_raw = str(data.get("intent", "")).lower().strip()
        intent = self._map_intent(intent_raw)
        if intent is None:
            intent = IntentType.GENERAL

        return RouteDecision(
            intent=intent,
            confidence=float(data.get("confidence", 0.5)),
            reasoning=str(data.get("reasoning", "")),
            suggested_agent=self.get_agent_for_intent(intent),
        )

    def _map_intent(self, intent_raw: str) -> IntentType | None:
        if intent_raw in INTENT_MAPPING:
            return INTENT_MAPPING[intent_raw]
        for key, val in INTENT_MAPPING.items():
            if key in intent_raw or intent_raw in key:
                return val
        return None

    def get_agent_for_intent(self, intent: IntentType) -> str:
        mapping = {
            IntentType.BILLING: "billing",
            IntentType.TECHNICAL: "technical",
            IntentType.REFUND: "refund",
            IntentType.GENERAL: "general",
            IntentType.ESCALATION: "escalation",
        }
        return mapping.get(intent, "general")
