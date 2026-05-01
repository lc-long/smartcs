from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field


class IntentType(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    REFUND = "refund"
    GENERAL = "general"
    ESCALATION = "escalation"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    HUMAN_AGENT = "human_agent"


class ConversationStatus(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    HUMAN_HANDLING = "human_handling"


class RouteDecision(BaseModel):
    intent: IntentType = Field(..., description="分类意图")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")
    reasoning: str = Field(..., description="分类理由")
    suggested_agent: str = Field(..., description="建议的Agent名称")


class ChatMessage(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    role: MessageRole
    content: str
    agent_name: str | None = None
    tools_called: list[str] = Field(default_factory=list)
    token_usage: dict | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    conversation_id: UUID | None = Field(None, description="会话ID，不传则创建新会话")
    customer_id: str = Field(..., min_length=1, description="客户ID")
    message: str = Field(..., min_length=1, max_length=5000, description="用户消息")
    stream: bool = Field(False, description="是否流式返回")


class ChatResponseMetadata(BaseModel):
    intent: IntentType
    confidence: float
    routing_reasoning: str
    model_used: str
    token_usage: dict
    latency_ms: int


class ChatResponse(BaseModel):
    conversation_id: UUID
    message: ChatMessage
    metadata: ChatResponseMetadata


class ConversationSummary(BaseModel):
    id: UUID
    customer_id: str
    status: ConversationStatus
    last_message: str
    last_agent: str | None = None
    created_at: datetime
    updated_at: datetime


class ConversationDetail(BaseModel):
    id: UUID
    customer_id: str
    status: ConversationStatus
    messages: list[ChatMessage]
    metadata: dict = Field(default_factory=dict)


class ApprovalRequest(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID
    approval_type: str
    amount: float | None = None
    reason: str
    customer_id: str
    context: dict = Field(default_factory=dict)
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.now)


class ApprovalDecision(BaseModel):
    decision: str = Field(..., pattern="^(approve|reject)$")
    comment: str = ""


def to_langchain_message(msg: ChatMessage) -> BaseMessage:
    if msg.role == MessageRole.USER:
        return HumanMessage(content=msg.content)
    elif msg.role == MessageRole.ASSISTANT:
        return AIMessage(content=msg.content)
    elif msg.role == MessageRole.SYSTEM:
        return SystemMessage(content=msg.content)
    else:
        return AIMessage(content=msg.content)


def from_langchain_message(msg: BaseMessage, agent_name: str | None = None) -> ChatMessage:
    if isinstance(msg, HumanMessage):
        role = MessageRole.USER
    elif isinstance(msg, AIMessage):
        role = MessageRole.ASSISTANT
    elif isinstance(msg, SystemMessage):
        role = MessageRole.SYSTEM
    else:
        role = MessageRole.ASSISTANT

    return ChatMessage(
        role=role,
        content=msg.content if isinstance(msg.content, str) else str(msg.content),
        agent_name=agent_name,
    )
