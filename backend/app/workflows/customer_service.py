from __future__ import annotations

import re
import uuid

import structlog
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from backend.app.agents.billing.agent import BillingAgent
from backend.app.agents.communication import get_communicator
from backend.app.agents.general.agent import GeneralAgent
from backend.app.agents.refund.agent import RefundAgent
from backend.app.agents.router.agent import RouterAgent
from backend.app.agents.supervisor.agent import SupervisorAgent
from backend.app.agents.technical.agent import TechnicalAgent
from backend.app.services.approval_queue import ApprovalItem, get_approval_queue
from backend.app.services.llm.provider import LLMProvider, get_llm_provider
from backend.app.workflows.state import CustomerServiceState

logger = structlog.get_logger()

HIGH_RISK_TOOLS = {"process_refund"}


class CustomerServiceWorkflow:
    def __init__(self, llm_provider: LLMProvider | None = None):
        self.llm_provider = llm_provider or get_llm_provider()

        # 创建所有Agent
        self.router = RouterAgent(self.llm_provider)
        self.supervisor = SupervisorAgent(self.llm_provider)
        self.billing = BillingAgent(self.llm_provider)
        self.technical = TechnicalAgent(self.llm_provider)
        self.refund = RefundAgent(self.llm_provider)
        self.general = GeneralAgent(self.llm_provider)

        # 初始化通信器
        self.communicator = get_communicator()
        self._register_agents()

        self._graph: CompiledStateGraph | None = None

    def _register_agents(self) -> None:
        """注册所有Agent到通信器"""
        self.communicator.register_agent("billing", self.billing)
        self.communicator.register_agent("technical", self.technical)
        self.communicator.register_agent("refund", self.refund)
        self.communicator.register_agent("general", self.general)

    def build_graph(self) -> CompiledStateGraph:
        if self._graph is not None:
            return self._graph

        graph = StateGraph(CustomerServiceState)

        # 添加节点
        graph.add_node("router", self._router_node)
        graph.add_node("execute", self._execute_node)
        graph.add_node("hitl_check", self._hitl_check_node)
        graph.add_node("response", self._response_node)

        # 添加边
        graph.add_edge(START, "router")
        graph.add_conditional_edges(
            "router",
            self._route_by_intent,
            {
                "billing": "execute",
                "technical": "execute",
                "refund": "execute",
                "general": "execute",
                "escalation": "response",
            },
        )
        graph.add_edge("execute", "hitl_check")
        graph.add_conditional_edges(
            "hitl_check",
            self._hitl_decision,
            {
                "needs_approval": "response",
                "no_approval": "response",
            },
        )
        graph.add_edge("response", END)

        self._graph = graph.compile()
        return self._graph

    async def run(
        self,
        messages: list,
        conversation_id: str,
        customer_id: str,
    ) -> CustomerServiceState:
        graph = self.build_graph()
        initial_state: CustomerServiceState = {
            "conversation_id": conversation_id,
            "customer_id": customer_id,
            "messages": messages,
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
            "trace_id": str(uuid.uuid4()),
        }
        result = await graph.ainvoke(initial_state)
        return result

    async def _router_node(self, state: CustomerServiceState) -> dict:
        """路由节点：分类意图并选择Agent"""
        messages = state["messages"]
        decision = await self.router.classify_intent(messages)

        logger.info(
            "router_decision",
            intent=decision.intent.value,
            confidence=decision.confidence,
            agent=decision.suggested_agent,
        )

        return {
            "current_intent": decision.intent.value,
            "routing_confidence": decision.confidence,
            "routing_reasoning": decision.reasoning,
            "active_agent": decision.suggested_agent,
        }

    def _route_by_intent(self, state: CustomerServiceState) -> str:
        """根据意图路由到对应处理节点"""
        intent = state["current_intent"]
        confidence = state["routing_confidence"]

        # 只有明确要求人工时才升级
        if intent == "escalation":
            return "escalation"

        # 低置信度时默认路由到通用Agent
        if confidence < 0.3:
            return "general"

        return intent

    async def _execute_node(self, state: CustomerServiceState) -> dict:
        """执行节点：调用对应的Agent处理任务"""
        messages = state["messages"]
        agent_name = state["active_agent"]
        customer_id = state.get("customer_id")

        # 获取对应的Agent
        agent_map = {
            "billing": self.billing,
            "technical": self.technical,
            "refund": self.refund,
            "general": self.general,
        }
        agent = agent_map.get(agent_name, self.general)

        logger.info("execute_agent", agent=agent_name, customer_id=customer_id)

        try:
            response = await agent.run(messages, customer_id=customer_id)
            content = response.content if isinstance(response.content, str) else str(response.content)
            content = self._strip_think_tags(content)

            tools_called = []
            if hasattr(response, "tool_calls") and response.tool_calls:
                tools_called = [tc["name"] for tc in response.tool_calls]

            logger.info("execute_success", agent=agent_name, tools=tools_called)

            return {
                "agent_response": content,
                "tools_called": tools_called,
            }
        except Exception as e:
            logger.exception("execute_error", agent=agent_name)
            return {
                "agent_response": f"抱歉，处理您的请求时出现了问题：{str(e)}",
            }

    @staticmethod
    def _strip_think_tags(content: str) -> str:
        return re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

    async def _hitl_check_node(self, state: CustomerServiceState) -> dict:
        tools_called = state.get("tools_called", [])
        has_high_risk = any(t in HIGH_RISK_TOOLS for t in tools_called)

        if not has_high_risk:
            return {}

        queue = get_approval_queue()
        approval = ApprovalItem(
            conversation_id=state["conversation_id"],
            approval_type="refund_approval",
            customer_id=state["customer_id"],
            agent_name=state["active_agent"],
            action_description=state["agent_response"],
            action_params={"tools_called": tools_called},
            risk_level="high",
        )
        queue.add(approval)

        logger.info(
            "hitl_approval_created",
            approval_id=str(approval.id),
            conversation_id=state["conversation_id"],
        )

        return {
            "needs_human": True,
            "agent_response": (
                f"{state['agent_response']}\n\n"
                f"[系统] 此操作需要人工审批，审批ID: {approval.id}"
            ),
        }

    def _hitl_decision(self, state: CustomerServiceState) -> str:
        if state.get("needs_human"):
            return "needs_approval"
        return "no_approval"

    async def _response_node(self, state: CustomerServiceState) -> dict:
        agent = state["active_agent"]
        intent = state["current_intent"]

        # 如果是升级请求，检查是否真的需要人工
        if intent == "escalation":
            # 检查用户是否明确要求人工
            messages = state["messages"]
            user_text = " ".join(
                m.content if hasattr(m, "content") else str(m)
                for m in messages
            )
            
            # 只有用户明确说"转人工"等关键词时才升级
            escalation_keywords = ["转人工", "找人工", "真人客服", "人工服务", "转接人工"]
            needs_human = any(kw in user_text for kw in escalation_keywords)
            
            if needs_human:
                return {
                    "agent_response": "您的问题需要人工客服处理，正在为您转接，请稍候...",
                    "active_agent": "escalation",
                    "needs_human": True,
                }
            else:
                # 不是明确要求人工，路由到通用Agent
                return {
                    "active_agent": "general",
                    "current_intent": "general",
                }

        logger.info(
            "workflow_complete",
            agent=agent,
            intent=intent,
            needs_human=state["needs_human"],
        )
        return {}


_workflow: CustomerServiceWorkflow | None = None


def get_workflow() -> CustomerServiceWorkflow:
    global _workflow
    if _workflow is None:
        _workflow = CustomerServiceWorkflow()
    return _workflow
