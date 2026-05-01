from __future__ import annotations

import structlog
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from backend.app.agents.base import BaseAgent
from backend.app.models.schemas import IntentType, RouteDecision
from backend.app.services.llm.provider import LLMProvider

logger = structlog.get_logger()

SYSTEM_PROMPT = """你是一个智能客服意图分类器。你的任务是分析用户消息，判断用户意图类别。

## 意图类别

1. **billing** - 账单相关：发票查询、支付历史、账单金额、付款问题
2. **technical** - 技术支持：产品故障、使用问题、功能咨询、Bug报告
3. **refund** - 退款相关：退款申请、退款进度、退款政策
4. **general** - 通用咨询：产品信息、公司信息、其他非特定问题
5. **escalation** - 人工升级：用户明确要求人工客服、情绪激动、问题复杂无法自动处理

## 判断规则

- 仔细分析用户消息中的关键词和上下文
- 如果有多重意图，选择最主要的一个
- 如果用户明确要求"人工"、"转人工"、"找人工"，直接归为 escalation
- 如果无法确定类别，归为 general
- 对你的分类给出置信度(0.0-1.0)和简短理由

请以JSON格式输出你的判断结果。"""


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
        except ValueError:
            logger.warning("router_parse_failed", raw_content=content)
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
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])

        data = json.loads(content)
        return RouteDecision(**data)

    def get_agent_for_intent(self, intent: IntentType) -> str:
        mapping = {
            IntentType.BILLING: "billing",
            IntentType.TECHNICAL: "technical",
            IntentType.REFUND: "refund",
            IntentType.GENERAL: "general",
            IntentType.ESCALATION: "escalation",
        }
        return mapping.get(intent, "general")
