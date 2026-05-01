from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from backend.app.agents.base import BaseAgent
from backend.app.services.llm.provider import LLMProvider

logger = structlog.get_logger()


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SubTask:
    id: str
    description: str
    assigned_agent: str
    status: TaskStatus = TaskStatus.PENDING
    result: str | None = None
    dependencies: list[str] = field(default_factory=list)
    priority: int = 0


@dataclass
class TaskPlan:
    original_request: str
    sub_tasks: list[SubTask]
    execution_order: list[list[str]]  # 并行组
    current_step: int = 0
    is_complex: bool = False
    reasoning: str = ""


class SupervisorAgent(BaseAgent):
    """Supervisor Agent - 负责任务拆解、规划和协调"""

    name = "supervisor"
    description = "任务规划者，负责分析复杂任务并协调多个Agent完成"

    PLANNING_PROMPT = """你是一个任务规划专家。分析用户请求，判断是否需要多个Agent协作完成。

可用的Agent：
- billing: 账单相关（发票、支付、扣费查询、账单核对）
- technical: 技术支持（故障排查、设备问题、知识库搜索、创建工单）
- refund: 退款处理（订单查询、退款判断、退款执行、退款状态查询）
- general: 通用问答（FAQ、公司信息、客户信息查询）

## 判断复杂任务的标准：
1. 用户请求涉及多个不同领域（如同时涉及退款和账单）
2. 用户请求需要多个步骤完成（如先查订单，再核对账单）
3. 用户请求涉及对比或汇总多个信息源

## 常见复杂任务场景：
- "我要退款，顺便查下账单" → refund + billing
- "订单有问题，帮我查下支付记录" → refund + billing
- "设备坏了，我要退货退款" → technical + refund
- "帮我核对下订单和支付是否匹配" → billing（使用order_payment_match工具）
- "我要投诉，找人工" → escalation

## 输出JSON格式：
{{
    "is_complex": true/false,
    "reasoning": "分析原因",
    "sub_tasks": [
        {{
            "id": "task_1",
            "description": "子任务描述",
            "agent": "agent_name",
            "dependencies": [],
            "priority": 1
        }}
    ],
    "execution_order": [["task_1"], ["task_2", "task_3"]]  // 并行组
}}"""

    AGGREGATION_PROMPT = """你是结果汇总专家。根据多个Agent的执行结果，生成最终回复。

用户原始请求：{original_request}

各Agent执行结果：
{agent_results}

## 汇总要求：
1. 将各Agent的结果整合成一个连贯的回复
2. 如果有冲突信息，以更详细的结果为准
3. 使用表格展示关键数据
4. 主动提供下一步建议
5. 保持专业友好的语气

请生成一个完整、连贯的回复给用户。"""

    def __init__(self, llm_provider: LLMProvider):
        super().__init__(llm_provider=llm_provider, temperature=0.1)

    async def run(self, messages: list[BaseMessage], **kwargs: dict) -> AIMessage:
        raise NotImplementedError("Use plan_task or aggregate_results instead")

    async def plan_task(self, user_message: str) -> TaskPlan:
        """分析任务复杂度，生成执行计划"""
        prompt = SystemMessage(content=self.PLANNING_PROMPT)
        user_msg = HumanMessage(content=user_message)

        response = await self.llm.ainvoke([prompt, user_msg])
        content = response.content if isinstance(response.content, str) else str(response.content)

        # 去除思考标签
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

        try:
            # 提取JSON
            first_brace = content.find("{")
            last_brace = content.rfind("}")
            if first_brace != -1 and last_brace != -1:
                data = json.loads(content[first_brace:last_brace + 1])

                sub_tasks = []
                for task_data in data.get("sub_tasks", []):
                    sub_tasks.append(SubTask(
                        id=task_data["id"],
                        description=task_data["description"],
                        assigned_agent=task_data["agent"],
                        dependencies=task_data.get("dependencies", []),
                        priority=task_data.get("priority", 0),
                    ))

                return TaskPlan(
                    original_request=user_message,
                    sub_tasks=sub_tasks,
                    execution_order=data.get("execution_order", []),
                    is_complex=data.get("is_complex", False),
                    reasoning=data.get("reasoning", ""),
                )
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("planning_parse_failed", error=str(e))

        # 默认作为简单任务
        return TaskPlan(
            original_request=user_message,
            sub_tasks=[],
            execution_order=[],
            is_complex=False,
            reasoning="无法解析，使用默认路由",
        )

    async def aggregate_results(
        self,
        original_request: str,
        agent_results: dict[str, str],
    ) -> str:
        """汇总多个Agent的结果，生成最终回复"""
        results_text = "\n".join(
            f"- {agent}: {result[:1000]}" for agent, result in agent_results.items()
        )

        prompt = SystemMessage(
            content=self.AGGREGATION_PROMPT.format(
                original_request=original_request,
                agent_results=results_text,
            )
        )
        user_msg = HumanMessage(content="请汇总结果并回复用户")

        response = await self.llm.ainvoke([prompt, user_msg])
        content = response.content if isinstance(response.content, str) else str(response.content)

        # 去除思考标签
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

        return content

    async def should_continue(
        self,
        original_request: str,
        current_results: dict[str, str],
        remaining_tasks: list[str],
    ) -> tuple[bool, str]:
        """判断是否需要继续执行，还是可以提前结束"""
        if not remaining_tasks:
            return False, "所有任务已完成"

        # 简单启发式：如果已有结果足够回答用户问题，可以提前结束
        results_summary = "\n".join(
            f"- {agent}: {result[:200]}" for agent, result in current_results.items()
        )

        prompt = SystemMessage(content=f"""根据已有结果，判断是否需要继续执行剩余任务。

用户请求：{original_request}

已有结果：
{results_summary}

剩余任务：{', '.join(remaining_tasks)}

请回答：
- 如果已有结果足够回答用户问题，输出：{{"continue": false, "reason": "原因"}}
- 如果需要继续执行，输出：{{"continue": true, "reason": "原因"}}

只输出JSON。""")

        response = await self.llm.ainvoke([prompt, HumanMessage(content="判断是否继续")])
        content = response.content if isinstance(response.content, str) else str(response.content)

        try:
            first_brace = content.find("{")
            last_brace = content.rfind("}")
            if first_brace != -1 and last_brace != -1:
                data = json.loads(content[first_brace:last_brace + 1])
                return data.get("continue", True), data.get("reason", "")
        except json.JSONDecodeError:
            pass

        return True, "默认继续执行"


_supervisor: SupervisorAgent | None = None


def get_supervisor(llm_provider=None) -> SupervisorAgent:
    global _supervisor
    if _supervisor is None:
        from backend.app.services.llm.provider import get_llm_provider
        _supervisor = SupervisorAgent(llm_provider or get_llm_provider())
    return _supervisor
