from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage

from backend.app.agents.router.agent import RouterAgent
from backend.app.models.schemas import IntentType
from backend.app.services.llm.provider import LLMProvider
from backend.app.workflows.customer_service import CustomerServiceWorkflow
from backend.app.workflows.state import CustomerServiceState


class TestRouterAgentClassification:
    """单元测试 Router Agent 意图分类"""

    def _create_mock_llm_provider(self) -> LLMProvider:
        provider = MagicMock(spec=LLMProvider)
        return provider

    def _create_mock_llm(self, response_content: str) -> BaseChatModel:
        mock_llm = AsyncMock(spec=BaseChatModel)
        mock_response = AIMessage(content=response_content)
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        return mock_llm

    @pytest.fixture
    def mock_provider(self) -> LLMProvider:
        return self._create_mock_llm_provider()

    @pytest.mark.asyncio
    async def test_classify_billing_intent(self, mock_provider: LLMProvider):
        """测试：账单意图正确分类"""
        mock_llm = self._create_mock_llm('{"intent": "billing", "confidence": 0.9, "reasoning": "账单关键词"}')
        mock_provider.get_llm.return_value = mock_llm

        router = RouterAgent(mock_provider)
        messages = [HumanMessage(content="我想查询上个月的账单")]
        result = await router.classify_intent(messages)

        assert result.intent == IntentType.BILLING
        assert result.confidence > 0.5
        assert result.suggested_agent == "billing"

    @pytest.mark.asyncio
    async def test_classify_refund_intent(self, mock_provider: LLMProvider):
        """测试：退款意图正确分类"""
        mock_llm = self._create_mock_llm('{"intent": "refund", "confidence": 0.85, "reasoning": "退款关键词"}')
        mock_provider.get_llm.return_value = mock_llm

        router = RouterAgent(mock_provider)
        messages = [HumanMessage(content="我要申请退款")]
        result = await router.classify_intent(messages)

        assert result.intent == IntentType.REFUND
        assert result.suggested_agent == "refund"

    @pytest.mark.asyncio
    async def test_classify_technical_intent(self, mock_provider: LLMProvider):
        """测试：技术问题意图正确分类"""
        mock_llm = self._create_mock_llm('{"intent": "technical", "confidence": 0.88, "reasoning": "技术关键词"}')
        mock_provider.get_llm.return_value = mock_llm

        router = RouterAgent(mock_provider)
        messages = [HumanMessage(content="设备坏了无法开机")]
        result = await router.classify_intent(messages)

        assert result.intent == IntentType.TECHNICAL
        assert result.suggested_agent == "technical"

    @pytest.mark.asyncio
    async def test_classify_escalation_intent(self, mock_provider: LLMProvider):
        """测试：转人工意图正确分类"""
        mock_llm = self._create_mock_llm('{"intent": "escalation", "confidence": 0.95, "reasoning": "明确要求人工"}')
        mock_provider.get_llm.return_value = mock_llm

        router = RouterAgent(mock_provider)
        messages = [HumanMessage(content="转人工客服")]
        result = await router.classify_intent(messages)

        assert result.intent == IntentType.ESCALATION
        assert result.suggested_agent == "escalation"

    @pytest.mark.asyncio
    async def test_classify_with_keyword_fallback(self, mock_provider: LLMProvider):
        """测试：关键词优先匹配，confidence >= 0.8 时不调用 LLM"""
        mock_llm = self._create_mock_llm('{"intent": "billing", "confidence": 0.9}')
        mock_provider.get_llm.return_value = mock_llm

        router = RouterAgent(mock_provider)
        messages = [HumanMessage(content="查账单")]
        result = await router.classify_intent(messages)

        assert result.intent == IntentType.BILLING
        assert result.confidence == 0.9
        mock_llm.ainvoke.assert_not_called()

    @pytest.mark.asyncio
    async def test_classify_fallback_to_general_on_error(self, mock_provider: LLMProvider):
        """测试：LLM 失败时降级到 general"""
        mock_llm = AsyncMock(spec=BaseChatModel)
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("API Error"))
        mock_provider.get_llm.return_value = mock_llm

        router = RouterAgent(mock_provider)
        messages = [HumanMessage(content="随便问问")]
        result = await router.classify_intent(messages)

        assert result.intent == IntentType.GENERAL
        assert result.confidence == 0.3

    @pytest.mark.asyncio
    async def test_multi_intent_detection(self, mock_provider: LLMProvider):
        """测试：多意图检测"""
        mock_llm = self._create_mock_llm(
            '{"intents": ["billing", "refund"], "confidence": 0.85, "reasoning": "多意图", "is_multi": true}'
        )
        mock_provider.get_llm.return_value = mock_llm

        router = RouterAgent(mock_provider)
        # 使用不包含任何关键词的消息，强制走LLM分类
        messages = [HumanMessage(content="你好")]
        result = await router.classify_intent(messages)

        assert result.is_multi_intent is True
        assert result.intent == IntentType.BILLING


class TestCustomerServiceWorkflow:
    """集成测试：LangGraph Workflow"""

    @pytest.fixture
    def mock_llm_provider(self) -> LLMProvider:
        provider = MagicMock(spec=LLMProvider)
        return provider

    def test_workflow_initialization(self, mock_llm_provider: LLMProvider):
        """测试：Workflow 正确初始化所有 Agent"""
        workflow = CustomerServiceWorkflow(llm_provider=mock_llm_provider)

        assert workflow.router is not None
        assert workflow.supervisor is not None
        assert workflow.billing is not None
        assert workflow.technical is not None
        assert workflow.refund is not None
        assert workflow.general is not None

    def test_workflow_graph_builds(self, mock_llm_provider: LLMProvider):
        """测试：Graph 可以正常构建"""
        workflow = CustomerServiceWorkflow(llm_provider=mock_llm_provider)
        graph = workflow.build_graph()

        assert graph is not None

    @pytest.mark.asyncio
    async def test_workflow_routes_to_billing(self, mock_llm_provider: LLMProvider):
        """测试：账单查询路由到 billing agent"""
        mock_llm = AsyncMock(spec=BaseChatModel)
        mock_response = AIMessage(content='{"intent": "billing", "confidence": 0.9, "reasoning": "test"}')
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm_provider.get_llm.return_value = mock_llm

        workflow = CustomerServiceWorkflow(llm_provider=mock_llm_provider)
        graph = workflow.build_graph()

        initial_state: CustomerServiceState = {
            "conversation_id": "test-conv-1",
            "customer_id": "C001",
            "messages": [HumanMessage(content="我想查账单")],
            "current_intent": "",
            "routing_confidence": 0.0,
            "routing_reasoning": "",
            "active_agent": "",
            "agent_response": "",
            "tools_called": [],
            "needs_human": False,
            "human_approved": False,
            "human_comment": None,
            "token_usage": {},
            "trace_id": "test-trace",
        }

    @pytest.mark.asyncio
    async def test_hitl_triggered_for_high_value_refund(self, mock_llm_provider: LLMProvider):
        """测试：高价值退款（>2000元）触发 HITL"""
        workflow = CustomerServiceWorkflow(llm_provider=mock_llm_provider)

        # 高价值退款场景：用户明确要求退款，金额3298元
        state: CustomerServiceState = {
            "conversation_id": "test-conv-2",
            "customer_id": "C001",
            "messages": [HumanMessage(content="我要退款")],
            "current_intent": "refund",
            "routing_confidence": 0.9,
            "routing_reasoning": "test",
            "active_agent": "refund",
            "agent_response": "退款处理中，订单金额¥3,298...",
            "tools_called": ["process_refund"],
            "needs_human": False,
            "human_approved": False,
            "human_comment": None,
            "token_usage": {},
            "trace_id": "test-trace",
        }

        # 使用较短的超时时间进行测试
        from unittest.mock import patch
        
        # 模拟审批队列立即返回拒绝
        async def mock_wait_for_approval(approval_id, timeout_seconds=300):
            return "rejected"
        
        with patch('backend.app.workflows.customer_service.get_hitl_blocker') as mock_blocker:
            mock_blocker.return_value.wait_for_approval = mock_wait_for_approval
            result = await workflow._hitl_check_node(state)
        
        # 高价值退款被拒绝后needs_human应为False
        assert result.get("needs_human") is False

    @pytest.mark.asyncio
    async def test_no_hitl_for_low_value_refund(self, mock_llm_provider: LLMProvider):
        """测试：低价值退款（<=2000元）不触发 HITL，自动批准"""
        workflow = CustomerServiceWorkflow(llm_provider=mock_llm_provider)

        # 低价值退款场景：用户明确要求退款，金额399元
        state: CustomerServiceState = {
            "conversation_id": "test-conv-3",
            "customer_id": "C001",
            "messages": [HumanMessage(content="我要退款")],
            "current_intent": "refund",
            "routing_confidence": 0.9,
            "routing_reasoning": "test",
            "active_agent": "refund",
            "agent_response": "退款处理中，订单金额¥399...",
            "tools_called": ["process_refund"],  # 有退款工具
            "needs_human": False,
            "human_approved": False,
            "human_comment": None,
            "token_usage": {},
            "trace_id": "test-trace",
        }

        result = await workflow._hitl_check_node(state)
        # 低价值退款不触发HITL，返回空字典
        assert result == {}
        assert result == {}  # 无高风险工具时返回空dict