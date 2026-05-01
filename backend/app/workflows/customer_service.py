from __future__ import annotations

import asyncio
import re
import uuid

import structlog
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from backend.app.agents.billing.agent import BillingAgent
from backend.app.agents.communication import AgentCommunicator, AgentMessage, get_communicator
from backend.app.agents.general.agent import GeneralAgent
from backend.app.agents.refund.agent import RefundAgent
from backend.app.agents.router.agent import RouterAgent
from backend.app.agents.supervisor.agent import SupervisorAgent
from backend.app.agents.technical.agent import TechnicalAgent
from backend.app.models.schemas import IntentType
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
        graph.add_node("supervisor", self._supervisor_node)
        graph.add_node("router", self._router_node)
        graph.add_node("simple_task", self._simple_task_node)
        graph.add_node("complex_task", self._complex_task_node)
        graph.add_node("parallel_execution", self._parallel_execution_node)
        graph.add_node("sequential_execution", self._sequential_execution_node)
        graph.add_node("aggregate", self._aggregate_node)
        graph.add_node("hitl_check", self._hitl_check_node)
        graph.add_node("response", self._response_node)

        # 添加边
        graph.add_edge(START, "supervisor")
        graph.add_conditional_edges(
            "supervisor",
            self._decide_execution_strategy,
            {
                "simple": "simple_task",
                "complex": "complex_task",
                "escalation": "response",
            },
        )
        graph.add_edge("simple_task", "hitl_check")
        graph.add_edge("complex_task", "aggregate")
        graph.add_edge("parallel_execution", "aggregate")
        graph.add_edge("sequential_execution", "aggregate")
        graph.add_edge("aggregate", "hitl_check")
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

    async def _supervisor_node(self, state: CustomerServiceState) -> dict:
        """Supervisor节点：分析任务复杂度，决定执行策略"""
        messages = state["messages"]
        user_text = " ".join(
            m.content if hasattr(m, "content") else str(m)
            for m in messages
        )

        logger.info("supervisor_analyzing", user_text=user_text[:200])

        # 分析任务
        analysis = await self.supervisor.decompose_task(user_text)

        # 同时进行意图分类（用于简单任务路由）
        decision = await self.router.classify_intent(messages)

        return {
            "current_intent": decision.intent.value,
            "routing_confidence": decision.confidence,
            "routing_reasoning": analysis.get("reasoning", ""),
            "active_agent": decision.suggested_agent,
        }

    def _decide_execution_strategy(self, state: CustomerServiceState) -> str:
        """决定执行策略：简单任务、复杂任务或升级"""
        intent = state["current_intent"]
        confidence = state["routing_confidence"]

        # 低置信度或升级请求
        if intent == "escalation" or confidence < 0.5:
            return "escalation"

        # 包含退款关键词的任务使用复杂流程
        messages = state["messages"]
        user_text = " ".join(
            m.content if hasattr(m, "content") else str(m)
            for m in messages
        )
        if "退款" in user_text and ("质量问题" in user_text or "故障" in user_text):
            return "complex"

        return "simple"

    async def _router_node(self, state: CustomerServiceState) -> dict:
        """路由节点：为简单任务选择Agent"""
        messages = state["messages"]
        decision = await self.router.classify_intent(messages)

        return {
            "current_intent": decision.intent.value,
            "routing_confidence": decision.confidence,
            "routing_reasoning": decision.reasoning,
            "active_agent": decision.suggested_agent,
        }

    async def _simple_task_node(self, state: CustomerServiceState) -> dict:
        """简单任务节点：单个Agent处理"""
        messages = state["messages"]
        agent_name = state["active_agent"]

        # 获取对应的Agent
        agent_map = {
            "billing": self.billing,
            "technical": self.technical,
            "refund": self.refund,
            "general": self.general,
        }
        agent = agent_map.get(agent_name, self.general)

        try:
            response = await agent.run(messages)
            content = response.content if isinstance(response.content, str) else str(response.content)
            content = self._strip_think_tags(content)

            tools_called = []
            if hasattr(response, "tool_calls") and response.tool_calls:
                tools_called = [tc["name"] for tc in response.tool_calls]

            return {
                "agent_response": content,
                "tools_called": tools_called,
            }
        except Exception:
            logger.exception("simple_task_error", agent=agent_name)
            return {
                "agent_response": "抱歉，处理您的请求时出现了问题，请稍后重试。",
            }

    async def _complex_task_node(self, state: CustomerServiceState) -> dict:
        """复杂任务节点：拆解并协调多Agent"""
        messages = state["messages"]
        user_text = " ".join(
            m.content if hasattr(m, "content") else str(m)
            for m in messages
        )

        # 重新分析获取详细的任务计划
        analysis = await self.supervisor.decompose_task(user_text)

        if not analysis.get("sub_tasks"):
            # 如果没有子任务，回退到简单处理
            return await self._simple_task_node(state)

        sub_tasks = analysis["sub_tasks"]
        execution_order = analysis.get("execution_order", [])

        # 执行子任务
        agent_results = {}

        if execution_order:
            # 按照指定顺序执行（支持并行）
            for parallel_group in execution_order:
                group_tasks = []
                for task_id in parallel_group:
                    task = next((t for t in sub_tasks if t["id"] == task_id), None)
                    if task:
                        group_tasks.append(task)

                if len(group_tasks) > 1:
                    # 并行执行
                    results = await self.communicator.broadcast(
                        sender="supervisor",
                        receivers=[t["agent"] for t in group_tasks],
                        content=user_text,
                        context={"task_description": "\n".join(t["description"] for t in group_tasks)},
                    )
                    for agent_name, response in results.items():
                        if response.success:
                            agent_results[agent_name] = response.content
                else:
                    # 单个任务
                    task = group_tasks[0]
                    response = await self.communicator.send_message(
                        AgentMessage(
                            sender="supervisor",
                            receiver=task["agent"],
                            content=task["description"],
                            context={"original_request": user_text},
                        )
                    )
                    if response.success:
                        agent_results[task["agent"]] = response.content
        else:
            # 默认并行执行所有任务
            results = await self.communicator.broadcast(
                sender="supervisor",
                receivers=[t["agent"] for t in sub_tasks],
                content=user_text,
            )
            for agent_name, response in results.items():
                if response.success:
                    agent_results[agent_name] = response.content

        return {
            "agent_response": str(agent_results),  # 临时存储，后续聚合
            "active_agent": "supervisor",
        }

    async def _parallel_execution_node(self, state: CustomerServiceState) -> dict:
        """并行执行节点"""
        # This is handled within complex_task_node
        return {}

    async def _sequential_execution_node(self, state: CustomerServiceState) -> dict:
        """串行执行节点"""
        # This is handled within complex_task_node
        return {}

    async def _aggregate_node(self, state: CustomerServiceState) -> dict:
        """聚合节点：汇总多Agent结果"""
        messages = state["messages"]
        user_text = " ".join(
            m.content if hasattr(m, "content") else str(m)
            for m in messages
        )

        # 获取各Agent的结果
        agent_response = state.get("agent_response", "{}")

        try:
            # 尝试解析为JSON
            import json
            agent_results = json.loads(agent_response)
        except (json.JSONDecodeError, TypeError):
            agent_results = {"general": agent_response}

        # 聚合结果
        final_response = await self.supervisor.aggregate_results(
            original_request=user_text,
            agent_results=agent_results,
        )

        return {
            "agent_response": final_response,
            "active_agent": "supervisor",
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
        logger.info(
            "workflow_complete",
            agent=state["active_agent"],
            intent=state["current_intent"],
            needs_human=state["needs_human"],
        )
        return {}


_workflow: CustomerServiceWorkflow | None = None


def get_workflow() -> CustomerServiceWorkflow:
    global _workflow
    if _workflow is None:
        _workflow = CustomerServiceWorkflow()
    return _workflow
