from __future__ import annotations

import asyncio
import json
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


@dataclass
class TaskPlan:
    original_request: str
    sub_tasks: list[SubTask]
    execution_order: list[list[str]]  # 并行组，每组内的任务可并行执行


class SupervisorAgent(BaseAgent):
    """Supervisor Agent - 负责任务拆解、协调和汇总"""

    name = "supervisor"
    description = "任务协调者，负责拆解复杂任务并协调多个Agent协作完成"

    DECOMPOSE_PROMPT = """你是一个任务分析专家。分析用户请求，判断是否需要多个Agent协作完成。

可用的Agent：
- billing: 账单相关（发票、支付、扣费查询）
- technical: 技术支持（故障排查、设备问题、知识库搜索）
- refund: 退款处理（订单查询、退款判断、退款执行）
- general: 通用问答（FAQ、公司信息）

对于简单任务，只分配一个Agent。
对于复杂任务，拆解成多个子任务，并指定执行顺序。

输出JSON格式：
{
    "is_complex": true/false,
    "reasoning": "分析原因",
    "sub_tasks": [
        {
            "id": "task_1",
            "description": "子任务描述",
            "agent": "agent_name",
            "dependencies": []
        }
    ],
    "execution_order": [["task_1"], ["task_2", "task_3"]]  // 并行组
}"""

    AGGREGATE_PROMPT = """你是一个结果汇总专家。根据多个Agent的执行结果，生成最终回复。

用户原始请求：{original_request}

各Agent执行结果：
{agent_results}

请生成一个完整、连贯的回复给用户。"""

    def __init__(self, llm_provider: LLMProvider):
        super().__init__(llm_provider=llm_provider, temperature=0.1)

    async def run(self, messages: list[BaseMessage], **kwargs: dict) -> AIMessage:
        raise NotImplementedError("Use decompose_task or aggregate_results instead")

    async def decompose_task(self, user_message: str) -> dict:
        """分析任务复杂度，决定是否需要多Agent协作"""
        prompt = SystemMessage(content=self.DECOMPOSE_PROMPT)
        user_msg = HumanMessage(content=user_message)

        response = await self.llm.ainvoke([prompt, user_msg])
        content = response.content if isinstance(response.content, str) else str(response.content)

        try:
            # 提取JSON
            first_brace = content.find("{")
            last_brace = content.rfind("}")
            if first_brace != -1 and last_brace != -1:
                result = json.loads(content[first_brace:last_brace + 1])
                return result
        except json.JSONDecodeError:
            pass

        # 默认作为简单任务处理
        return {
            "is_complex": False,
            "reasoning": "无法解析，使用默认路由",
            "sub_tasks": [],
            "execution_order": [],
        }

    async def aggregate_results(
        self,
        original_request: str,
        agent_results: dict[str, str],
    ) -> str:
        """汇总多个Agent的结果，生成最终回复"""
        results_text = "\n".join(
            f"- {agent}: {result}" for agent, result in agent_results.items()
        )

        prompt = SystemMessage(
            content=self.AGGREGATE_PROMPT.format(
                original_request=original_request,
                agent_results=results_text,
            )
        )
        user_msg = HumanMessage(content="请汇总结果并回复用户")

        response = await self.llm.ainvoke([prompt, user_msg])
        content = response.content if isinstance(response.content, str) else str(response.content)

        # 去除think标签
        import re
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

        return content
