from __future__ import annotations

import re
import uuid

import structlog

from backend.app.agents.service_agent import ServiceAgent
from backend.app.services.approval_queue import ApprovalItem, get_approval_queue
from backend.app.services.hitl_blocker import get_hitl_blocker
from backend.app.services.llm.provider import LLMProvider, get_llm_provider

logger = structlog.get_logger()


class ServiceWorkflow:
    def __init__(self, llm_provider: LLMProvider | None = None):
        self.llm_provider = llm_provider or get_llm_provider()
        self.agent = ServiceAgent(self.llm_provider)

    async def run(
        self,
        messages: list,
        conversation_id: str,
        customer_id: str,
        emit_callback=None,
    ) -> dict:
        """运行客服工作流：Agent处理 + HITL检查"""
        start_time = None
        try:
            import time

            start_time = time.time()

            # 调用Agent处理
            agent_response, tools_called = await self._run_agent(messages, customer_id)

            int((time.time() - start_time) * 1000)

            # HITL检查
            needs_human, human_approved = await self._check_hitl(
                tools_called, agent_response, conversation_id, customer_id, emit_callback
            )

            # 构建结果
            result = {
                "conversation_id": conversation_id,
                "customer_id": customer_id,
                "agent_response": agent_response,
                "current_intent": "service",
                "routing_confidence": 1.0,
                "routing_reasoning": "单Agent架构直接处理",
                "active_agent": "service",
                "tools_called": tools_called,
                "needs_human": needs_human,
                "human_approved": human_approved,
                "token_usage": {},
                "trace_id": str(uuid.uuid4()),
            }

            if emit_callback and needs_human:
                await emit_callback(
                    "human_approval_needed",
                    {
                        "reason": agent_response,
                        "conversation_id": conversation_id,
                    },
                )

            return result

        except Exception:
            logger.exception("workflow_error", conversation_id=conversation_id)
            return {
                "conversation_id": conversation_id,
                "customer_id": customer_id,
                "agent_response": "抱歉，处理您的请求时出现错误，请稍后重试。",
                "current_intent": "service",
                "routing_confidence": 0,
                "routing_reasoning": "处理出错",
                "active_agent": "service",
                "tools_called": [],
                "needs_human": False,
                "human_approved": False,
                "token_usage": {},
                "trace_id": str(uuid.uuid4()),
            }

    async def _run_agent(
        self,
        messages: list,
        customer_id: str | None,
    ) -> tuple[str, list[str]]:
        """调用Agent处理消息"""
        response, tools_called = await self.agent.run(messages, customer_id=customer_id)
        response_content = response.content if hasattr(response, "content") else str(response)
        return response_content, tools_called

    async def _check_hitl(
        self,
        tools_called: list[str],
        agent_response: str,
        conversation_id: str,
        customer_id: str,
        emit_callback=None,
    ) -> tuple[bool, bool]:
        """检查是否需要人工审批"""
        high_risk_tools = {"process_refund"}

        has_high_risk = any(tool in high_risk_tools for tool in tools_called)
        if not has_high_risk:
            return False, False

        # 提取退款金额
        refund_amount = self._extract_refund_amount(agent_response)

        # 判断是否需要审批
        needs_approval = refund_amount > 2000

        if not needs_approval:
            logger.info("hitl_auto_approved", refund_amount=refund_amount)
            return False, True

        # 创建审批请求
        queue = get_approval_queue()
        approval = ApprovalItem(
            conversation_id=conversation_id,
            approval_type="refund_approval",
            customer_id=customer_id,
            agent_name="service",
            action_description=f"高价值退款（¥{refund_amount}），需要人工审批",
            action_params={
                "tools_called": tools_called,
                "refund_amount": refund_amount,
            },
            risk_level="high",
        )
        queue.add(approval)
        approval_id = str(approval.id)

        logger.info("hitl_approval_required", approval_id=approval_id, refund_amount=refund_amount)

        if emit_callback:
            await emit_callback(
                "hitl_waiting",
                {
                    "approval_id": approval_id,
                    "message": f"[系统] 高价值退款（¥{refund_amount}），审批ID: {approval_id}",
                },
            )

        # 阻塞等待审批（最长5分钟）
        blocker = get_hitl_blocker()
        decision = await blocker.wait_for_approval(approval_id, timeout_seconds=300)

        human_approved = decision == "approved"
        return True, human_approved

    def _extract_refund_amount(self, text: str) -> float:
        """从文本中提取退款金额"""
        patterns = [
            r"¥([\d,]+(?:\.\d{2})?)",
            r"([\d,]+(?:\.\d{2})?)元",
            r"退款[^\d]*([\d,]+(?:\.\d{2})?)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                amount_str = match.group(1).replace(",", "")
                try:
                    return float(amount_str)
                except ValueError:
                    continue

        return 0.0


_workflow: ServiceWorkflow | None = None


def get_workflow() -> ServiceWorkflow:
    global _workflow
    if _workflow is None:
        _workflow = ServiceWorkflow()
    return _workflow
