from __future__ import annotations

from typing import Literal

import structlog
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from backend.app.agents.router.agent import RouterAgent
from backend.app.models.schemas import IntentType
from backend.app.services.llm.provider import LLMProvider, get_llm_provider
from backend.app.workflows.state import CustomerServiceState

logger = structlog.get_logger()


class CustomerServiceWorkflow:
    def __init__(self, llm_provider: LLMProvider | None = None):
        self.llm_provider = llm_provider or get_llm_provider()
        self.router = RouterAgent(self.llm_provider)
        self._graph: CompiledStateGraph | None = None

    def build_graph(self) -> CompiledStateGraph:
        if self._graph is not None:
            return self._graph

        graph = StateGraph(CustomerServiceState)

        graph.add_node("router", self._router_node)
        graph.add_node("billing", self._billing_node)
        graph.add_node("technical", self._technical_node)
        graph.add_node("refund", self._refund_node)
        graph.add_node("general", self._general_node)
        graph.add_node("escalation", self._escalation_node)
        graph.add_node("response", self._response_node)

        graph.add_edge(START, "router")
        graph.add_conditional_edges(
            "router",
            self._route_by_intent,
            {
                "billing": "billing",
                "technical": "technical",
                "refund": "refund",
                "general": "general",
                "escalation": "escalation",
            },
        )
        graph.add_edge("billing", "response")
        graph.add_edge("technical", "response")
        graph.add_edge("refund", "response")
        graph.add_edge("general", "response")
        graph.add_edge("escalation", "response")
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
            "trace_id": "",
        }
        result = await graph.ainvoke(initial_state)
        return result

    async def _router_node(self, state: CustomerServiceState) -> dict:
        messages = state["messages"]
        decision = await self.router.classify_intent(messages)

        return {
            "current_intent": decision.intent.value,
            "routing_confidence": decision.confidence,
            "routing_reasoning": decision.reasoning,
            "active_agent": decision.suggested_agent,
        }

    def _route_by_intent(self, state: CustomerServiceState) -> str:
        intent = state["current_intent"]
        confidence = state["routing_confidence"]

        if confidence < 0.5:
            logger.info("low_confidence_escalation", confidence=confidence)
            return "escalation"

        return intent

    async def _billing_node(self, state: CustomerServiceState) -> dict:
        logger.info("agent_node", agent="billing")
        model_name = self.llm_provider.get_model_for_agent("billing")
        llm = self.llm_provider.get_llm(model_name=model_name)
        response = await llm.ainvoke(state["messages"])
        content = response.content if isinstance(response.content, str) else str(response.content)
        return {"agent_response": content, "active_agent": "billing"}

    async def _technical_node(self, state: CustomerServiceState) -> dict:
        logger.info("agent_node", agent="technical")
        model_name = self.llm_provider.get_model_for_agent("technical")
        llm = self.llm_provider.get_llm(model_name=model_name)
        response = await llm.ainvoke(state["messages"])
        content = response.content if isinstance(response.content, str) else str(response.content)
        return {"agent_response": content, "active_agent": "technical"}

    async def _refund_node(self, state: CustomerServiceState) -> dict:
        logger.info("agent_node", agent="refund")
        model_name = self.llm_provider.get_model_for_agent("refund")
        llm = self.llm_provider.get_llm(model_name=model_name)
        response = await llm.ainvoke(state["messages"])
        content = response.content if isinstance(response.content, str) else str(response.content)
        return {"agent_response": content, "active_agent": "refund"}

    async def _general_node(self, state: CustomerServiceState) -> dict:
        logger.info("agent_node", agent="general")
        model_name = self.llm_provider.get_model_for_agent("general")
        llm = self.llm_provider.get_llm(model_name=model_name)
        response = await llm.ainvoke(state["messages"])
        content = response.content if isinstance(response.content, str) else str(response.content)
        return {"agent_response": content, "active_agent": "general"}

    async def _escalation_node(self, state: CustomerServiceState) -> dict:
        logger.info("agent_node", agent="escalation")
        return {
            "agent_response": "您的问题需要人工客服处理，正在为您转接，请稍候...",
            "active_agent": "escalation",
            "needs_human": True,
        }

    async def _response_node(self, state: CustomerServiceState) -> dict:
        logger.info(
            "workflow_complete",
            agent=state["active_agent"],
            intent=state["current_intent"],
        )
        return {}


_workflow: CustomerServiceWorkflow | None = None


def get_workflow() -> CustomerServiceWorkflow:
    global _workflow
    if _workflow is None:
        _workflow = CustomerServiceWorkflow()
    return _workflow
