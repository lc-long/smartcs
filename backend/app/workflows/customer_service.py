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
from backend.app.agents.supervisor.agent import SupervisorAgent, get_supervisor
from backend.app.agents.technical.agent import TechnicalAgent
from backend.app.models.schemas import IntentType
from backend.app.services.approval_queue import ApprovalItem, get_approval_queue
from backend.app.services.llm.provider import LLMProvider, get_llm_provider
from backend.app.services.memory.working import WorkingMemory, WorkingMemoryStore, get_working_memory_store
from backend.app.workflows.state import CustomerServiceState

logger = structlog.get_logger()

HIGH_RISK_TOOLS = {"process_refund"}


class CustomerServiceWorkflow:
    def __init__(self, llm_provider: LLMProvider | None = None):
        self.llm_provider = llm_provider or get_llm_provider()

        # 创建所有Agent
        self.router = RouterAgent(self.llm_provider)
        self.supervisor = get_supervisor(self.llm_provider)
        self.billing = BillingAgent(self.llm_provider)
        self.technical = TechnicalAgent(self.llm_provider)
        self.refund = RefundAgent(self.llm_provider)
        self.general = GeneralAgent(self.llm_provider)

        # 初始化通信器和记忆存储
        self.communicator = get_communicator()
        self.memory_store = get_working_memory_store()
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
        graph.add_node("planner", self._planner_node)
        graph.add_node("execute_simple", self._execute_simple_node)
        graph.add_node("execute_complex", self._execute_complex_node)
        graph.add_node("aggregate", self._aggregate_node)
        graph.add_node("hitl_check", self._hitl_check_node)
        graph.add_node("response", self._response_node)

        # 添加边
        graph.add_edge(START, "planner")
        graph.add_conditional_edges(
            "planner",
            self._decide_execution_strategy,
            {
                "simple": "execute_simple",
                "complex": "execute_complex",
                "escalation": "response",
            },
        )
        graph.add_edge("execute_simple", "hitl_check")
        graph.add_edge("execute_complex", "aggregate")
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

        # 创建工作记忆
        user_text = " ".join(
            m.content if hasattr(m, "content") else str(m) for m in messages
        )
        working_memory = self.memory_store.create(
            conversation_id=conversation_id,
            customer_id=customer_id,
            original_request=user_text,
        )

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

        # 保存最终响应到工作记忆
        working_memory.final_response = result.get("agent_response", "")
        working_memory.is_complete = True

        return result

    async def _planner_node(self, state: CustomerServiceState) -> dict:
        """规划节点：分析任务复杂度，生成执行计划"""
        messages = state["messages"]
        user_text = " ".join(
            m.content if hasattr(m, "content") else str(m) for m in messages
        )

        # 获取工作记忆
        conversation_id = state["conversation_id"]
        working_memory = self.memory_store.get(conversation_id)

        logger.info("planner_analyzing", user_text=user_text[:200])

        # 使用Supervisor进行任务规划
        plan = await self.supervisor.plan_task(user_text)

        # 保存计划到工作记忆
        if working_memory:
            working_memory.current_plan = {
                "is_complex": plan.is_complex,
                "reasoning": plan.reasoning,
                "sub_tasks": [
                    {
                        "id": t.id,
                        "description": t.description,
                        "agent": t.assigned_agent,
                        "dependencies": t.dependencies,
                    }
                    for t in plan.sub_tasks
                ],
            }
            working_memory.add_thought(
                f"任务分析：{'复杂任务' if plan.is_complex else '简单任务'}。{plan.reasoning}",
                agent="supervisor",
            )

        # 同时进行意图分类（用于简单任务路由）
        decision = await self.router.classify_intent(messages)

        return {
            "current_intent": decision.intent.value,
            "routing_confidence": decision.confidence,
            "routing_reasoning": plan.reasoning,
            "active_agent": decision.suggested_agent,
        }

    def _decide_execution_strategy(self, state: CustomerServiceState) -> str:
        """决定执行策略"""
        intent = state["current_intent"]
        confidence = state["routing_confidence"]

        # 获取工作记忆中的计划
        conversation_id = state["conversation_id"]
        working_memory = self.memory_store.get(conversation_id)

        if working_memory and working_memory.current_plan:
            if working_memory.current_plan.get("is_complex"):
                return "complex"

        # 只有明确要求人工时才升级
        if intent == "escalation":
            return "escalation"

        # 低置信度时默认路由到通用Agent
        if confidence < 0.3:
            return "general"

        return "simple"

    async def _execute_simple_node(self, state: CustomerServiceState) -> dict:
        """简单任务执行节点"""
        messages = state["messages"]
        agent_name = state["active_agent"]
        customer_id = state.get("customer_id")
        conversation_id = state["conversation_id"]

        # 获取工作记忆
        working_memory = self.memory_store.get(conversation_id)

        # 获取对应的Agent
        agent_map = {
            "billing": self.billing,
            "technical": self.technical,
            "refund": self.refund,
            "general": self.general,
        }
        agent = agent_map.get(agent_name, self.general)

        logger.info("execute_simple", agent=agent_name, customer_id=customer_id)

        # 记录到工作记忆
        if working_memory:
            working_memory.add_thought(
                f"选择 {agent_name} Agent 处理请求",
                agent="router",
            )

        try:
            response = await agent.run(messages, customer_id=customer_id)
            content = response.content if isinstance(response.content, str) else str(response.content)
            content = self._strip_think_tags(content)

            tools_called = []
            if hasattr(response, "tool_calls") and response.tool_calls:
                tools_called = [tc["name"] for tc in response.tool_calls]

            # 记录结果到工作记忆
            if working_memory:
                working_memory.add_result(content, agent_name)
                for tool in tools_called:
                    working_memory.add_action(
                        f"调用工具: {tool}",
                        tool=tool,
                        agent=agent_name,
                    )

            logger.info("execute_simple_success", agent=agent_name, tools=tools_called)

            return {
                "agent_response": content,
                "tools_called": tools_called,
            }
        except Exception as e:
            logger.exception("execute_simple_error", agent=agent_name)
            error_msg = f"抱歉，处理您的请求时出现了问题：{str(e)}"
            if working_memory:
                working_memory.add_observation(f"执行失败: {str(e)}", agent=agent_name)
            return {
                "agent_response": error_msg,
            }

    async def _execute_complex_node(self, state: CustomerServiceState) -> dict:
        """复杂任务执行节点"""
        messages = state["messages"]
        customer_id = state.get("customer_id")
        conversation_id = state["conversation_id"]

        # 获取工作记忆
        working_memory = self.memory_store.get(conversation_id)

        if not working_memory or not working_memory.current_plan:
            # 没有计划，回退到简单执行
            return await self._execute_simple_node(state)

        plan = working_memory.current_plan
        sub_tasks = plan.get("sub_tasks", [])

        if not sub_tasks:
            return await self._execute_simple_node(state)

        logger.info("execute_complex", task_count=len(sub_tasks))

        # 执行子任务
        agent_results = {}
        all_tools_called = []

        # 按执行顺序执行
        execution_order = plan.get("execution_order", [])

        if execution_order:
            for parallel_group in execution_order:
                group_tasks = [
                    t for t in sub_tasks if t["id"] in parallel_group
                ]

                if len(group_tasks) > 1:
                    # 并行执行
                    tasks = []
                    for task in group_tasks:
                        tasks.append(self._execute_subtask(
                            task, messages, customer_id, working_memory
                        ))
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    for i, result in enumerate(results):
                        task = group_tasks[i]
                        if isinstance(result, Exception):
                            agent_results[task["agent"]] = f"执行失败: {str(result)}"
                        else:
                            agent_results[task["agent"]] = result
                else:
                    # 单个任务
                    task = group_tasks[0]
                    result = await self._execute_subtask(
                        task, messages, customer_id, working_memory
                    )
                    agent_results[task["agent"]] = result
        else:
            # 默认并行执行所有任务
            tasks = []
            for task in sub_tasks:
                tasks.append(self._execute_subtask(
                    task, messages, customer_id, working_memory
                ))
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results):
                task = sub_tasks[i]
                if isinstance(result, Exception):
                    agent_results[task["agent"]] = f"执行失败: {str(result)}"
                else:
                    agent_results[task["agent"]] = result

        # 检查是否可以提前结束
        should_continue, reason = await self.supervisor.should_continue(
            working_memory.original_request,
            agent_results,
            [],  # 所有任务已执行
        )

        if working_memory:
            working_memory.add_thought(
                f"所有子任务执行完成，准备汇总结果",
                agent="supervisor",
            )

        return {
            "agent_response": str(agent_results),
            "active_agent": "supervisor",
        }

    async def _execute_subtask(
        self,
        task: dict,
        messages: list,
        customer_id: str,
        working_memory: WorkingMemory,
    ) -> str:
        """执行单个子任务"""
        agent_name = task["agent"]
        agent_map = {
            "billing": self.billing,
            "technical": self.technical,
            "refund": self.refund,
            "general": self.general,
        }
        agent = agent_map.get(agent_name, self.general)

        if working_memory:
            working_memory.add_thought(
                f"开始执行子任务: {task['description']}",
                agent=agent_name,
            )

        try:
            response = await agent.run(messages, customer_id=customer_id)
            content = response.content if isinstance(response.content, str) else str(response.content)
            content = self._strip_think_tags(content)

            if working_memory:
                working_memory.add_result(content, agent_name)

            return content
        except Exception as e:
            logger.exception("subtask_error", agent=agent_name)
            if working_memory:
                working_memory.add_observation(f"子任务执行失败: {str(e)}", agent=agent_name)
            return f"执行失败: {str(e)}"

    async def _aggregate_node(self, state: CustomerServiceState) -> dict:
        """聚合节点：汇总多Agent结果"""
        messages = state["messages"]
        conversation_id = state["conversation_id"]

        # 获取工作记忆
        working_memory = self.memory_store.get(conversation_id)

        if not working_memory:
            return {"agent_response": "抱歉，处理过程中出现问题"}

        # 获取各Agent的结果
        agent_results = working_memory.get_agent_results()

        if not agent_results:
            return {"agent_response": state.get("agent_response", "抱歉，无法获取处理结果")}

        # 使用Supervisor汇总结果
        final_response = await self.supervisor.aggregate_results(
            working_memory.original_request,
            agent_results,
        )

        if working_memory:
            working_memory.add_thought(
                f"汇总 {len(agent_results)} 个Agent的结果",
                agent="supervisor",
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
        agent = state["active_agent"]
        intent = state["current_intent"]

        # 如果是升级请求
        if intent == "escalation":
            messages = state["messages"]
            user_text = " ".join(
                m.content if hasattr(m, "content") else str(m) for m in messages
            )

            escalation_keywords = ["转人工", "找人工", "真人客服", "人工服务", "转接人工"]
            needs_human = any(kw in user_text for kw in escalation_keywords)

            if needs_human:
                return {
                    "agent_response": "您的问题需要人工客服处理，正在为您转接，请稍候...",
                    "active_agent": "escalation",
                    "needs_human": True,
                }
            else:
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
