# SmartCS - 架构设计文档

## 1. 系统架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│          React + TypeScript + WebSocket                      │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐                  │
│  │ 对话界面  │  │ 管理后台  │  │ 数据看板  │                  │
│  └──────────┘  └──────────┘  └───────────┘                  │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP / WebSocket
┌────────────────────────┼────────────────────────────────────┐
│                    FastAPI Backend                            │
│  ┌─────────────────────┼────────────────────────────────┐   │
│  │              API Layer                                │   │
│  │   /api/v1/chat  /api/v1/conversations  /ws/chat      │   │
│  └─────────────────────┬────────────────────────────────┘   │
│                        │                                     │
│  ┌─────────────────────┼────────────────────────────────┐   │
│  │           LangGraph Workflow Engine                    │   │
│  │                                                      │   │
│  │    ┌──────────────┐                                  │   │
│  │    │ Router Agent  │ ← 意图分类 (GPT-4o-mini)       │   │
│  │    └──────┬───────┘                                  │   │
│  │           │                                          │   │
│  │    ┌──────┼──────┬──────────┐                        │   │
│  │    ▼      ▼      ▼          ▼                        │   │
│  │  账单    技术    退款      通用问答                    │   │
│  │  Agent  Agent   Agent     Agent                      │   │
│  │    │      │      │          │                        │   │
│  │    └──────┴──────┴──────────┘                        │   │
│  │              │                                        │   │
│  │       ┌──────┴──────┐                                │   │
│  │       │  Evaluator   │ ← 质量评估                    │   │
│  │       └──────┬──────┘                                │   │
│  │              │                                        │   │
│  │       ┌──────┴──────┐                                │   │
│  │       │ HITL Handler │ ← Human-in-the-Loop          │   │
│  │       └─────────────┘                                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Services Layer                           │   │
│  │  ┌────────┐ ┌────────┐ ┌──────────┐ ┌────────────┐  │   │
│  │  │LLM     │ │Memory  │ │Knowledge │ │Observability│  │   │
│  │  │Provider │ │Service │ │Service   │ │Service     │  │   │
│  │  └────────┘ └────────┘ └──────────┘ └────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    ┌─────────┐    ┌──────────┐    ┌──────────┐
    │  Redis   │    │PostgreSQL│    │  Chroma   │
    │ (会话状态)│    │ (持久数据)│    │ (向量库)  │
    └─────────┘    └──────────┘    └──────────┘
```

## 2. 核心架构决策

### 2.1 为什么选择 LangGraph

| 维度 | LangGraph | CrewAI | AutoGen |
|------|-----------|--------|---------|
| 生产就绪度 | 最高（持久化执行、检查点） | 良好 | 中等 |
| 控制粒度 | 最高（图原语） | 中等（约定式） | 高（双层架构） |
| 客服场景适配 | 优秀（路由、人工介入） | 良好 | 良好 |
| 可观测性 | LangSmith（商业） | OpenTelemetry | 日志+追踪 |
| 企业采用 | Klarna、Uber、J.P. Morgan | 增长中 | 研究为主 |

**决策**：选择 LangGraph，因为：
- 持久化执行（durable execution）是企业级客服的刚需
- 检查点（checkpointing）支持故障恢复
- Human-in-the-loop 原生支持
- 被多家大厂验证过生产可靠性

### 2.2 为什么选择多Agent而非单Agent

单Agent方案的问题：
- 提示词膨胀：所有工具和职责塞在一个prompt里，上下文窗口浪费
- 工具混淆：Agent在大量工具中选错工具的概率随工具数量指数增长
- 难以独立优化：改一个场景的提示词可能影响其他场景

多Agent优势：
- 关注点分离：每个Agent只处理一类意图，提示词精简
- 独立优化：不同Agent可以使用不同模型、不同提示词
- 可扩展：新增业务场景只需新增Agent，不影响现有系统

### 2.3 模型路由策略

```
用户请求复杂度评估
       │
       ├── 简单 (问候、FAQ、状态查询) → GPT-4o-mini / Claude Haiku
       │   成本: ~$0.0001/请求
       │
       ├── 中等 (账单问题、技术排查) → GPT-4o / Claude Sonnet
       │   成本: ~$0.001/请求
       │
       └── 复杂 (退款决策、多步骤推理) → GPT-4o / Claude Opus
           成本: ~$0.01/请求
```

## 3. Agent 详细设计

### 3.1 Router Agent（路由Agent）

**职责**：分析用户输入，分类意图，路由到对应专家Agent

**输入**：用户消息 + 会话历史
**输出**：
```python
class RouteDecision(BaseModel):
    intent: IntentType          # billing | technical | refund | general | escalation
    confidence: float           # 0.0 - 1.0
    reasoning: str              # 分类理由
    suggested_agent: str        # 目标Agent名称
```

**路由规则**：
- confidence >= 0.8 → 直接路由到目标Agent
- 0.5 <= confidence < 0.8 → 路由到目标Agent，但标记需要验证
- confidence < 0.5 → 升级到人工（escalation）

### 3.2 BillingAgent（账单Agent）

**职责**：处理账单相关查询

**工具集**：
| 工具 | 功能 | 风险等级 |
|------|------|----------|
| `invoice_lookup` | 查询发票信息 | 低 |
| `payment_history` | 查询支付历史 | 低 |
| `billing_summary` | 生成账单摘要 | 低 |

**对话流程**：
```
用户: "我上个月的账单金额不对"
  → Agent调用 invoice_lookup(customer_id, last_month)
  → Agent对比用户描述和实际账单
  → Agent解释差异或确认问题
  → 如需调整，标记为需要人工审批
```

### 3.3 TechnicalAgent（技术Agent）

**职责**：处理技术支持问题

**工具集**：
| 工具 | 功能 | 风险等级 |
|------|------|----------|
| `knowledge_search` | 知识库语义检索 | 低 |
| `ticket_create` | 创建技术工单 | 中 |
| `ticket_update` | 更新工单状态 | 中 |
| `product_info` | 查询产品信息 | 低 |

### 3.4 RefundAgent（退款Agent）

**职责**：处理退款请求

**工具集**：
| 工具 | 功能 | 风险等级 | 需要审批 |
|------|------|----------|----------|
| `order_lookup` | 查询订单信息 | 低 | 否 |
| `refund_eligibility` | 检查退款资格 | 低 | 否 |
| `process_refund` | 执行退款 | **高** | **是** |

**Human-in-the-Loop 触发条件**：
- 退款金额 > ¥500
- 订单创建时间 > 30天
- 同一用户30天内退款次数 > 2

### 3.5 GeneralAgent（通用Agent）

**职责**：处理无法分类到其他Agent的通用查询

**工具集**：
| 工具 | 功能 |
|------|------|
| `faq_search` | FAQ检索 |
| `product_info` | 产品信息查询 |
| `company_info` | 公司信息查询 |

## 4. LangGraph 工作流设计

### 4.1 状态定义

```python
class CustomerServiceState(TypedDict):
    # 会话信息
    conversation_id: str
    customer_id: str
    messages: list[BaseMessage]

    # 路由状态
    current_intent: IntentType
    routing_confidence: float
    routing_reasoning: str

    # Agent执行状态
    active_agent: str
    agent_response: str
    tools_called: list[str]

    # 人工介入状态
    needs_human: bool
    human_approved: bool
    human_comment: str | None

    # 元数据
    token_usage: dict
    trace_id: str
```

### 4.2 图结构

```python
workflow = StateGraph(CustomerServiceState)

# 添加节点
workflow.add_node("router", router_agent)
workflow.add_node("billing", billing_agent)
workflow.add_node("technical", technical_agent)
workflow.add_node("refund", refund_agent)
workflow.add_node("general", general_agent)
workflow.add_node("evaluator", quality_evaluator)
workflow.add_node("human_approval", human_approval_handler)
workflow.add_node("response", response_formatter)

# 添加边
workflow.add_edge(START, "router")
workflow.add_conditional_edges(
    "router",
    route_by_intent,
    {
        "billing": "billing",
        "technical": "technical",
        "refund": "refund",
        "general": "general",
        "escalation": "human_approval",
    }
)
workflow.add_edge("billing", "evaluator")
workflow.add_edge("technical", "evaluator")
workflow.add_edge("refund", "evaluator")
workflow.add_edge("general", "evaluator")
workflow.add_conditional_edges(
    "evaluator",
    evaluate_quality,
    {
        "approved": "response",
        "needs_human": "human_approval",
        "retry": "router",  # 重试路由
    }
)
workflow.add_edge("human_approval", "response")
workflow.add_edge("response", END)
```

### 4.3 检查点与持久化

```python
from langgraph.checkpoint.redis import RedisSaver

checkpointer = RedisSaver.from_url(redis_url)
app = workflow.compile(checkpointer=checkpointer)
```

每次执行步骤后自动保存状态，支持：
- 故障后从最后检查点恢复
- Human-in-the-loop 暂停/恢复
- 会话历史回溯

## 5. 数据存储设计

### 5.1 Redis — 会话状态

```
conversation:{id}:state     → LangGraph检查点状态
conversation:{id}:messages  → 当前会话消息列表
customer:{id}:sessions      → 客户活跃会话集合
```

### 5.2 PostgreSQL — 持久数据

**核心表**：
```sql
-- 会话表
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    customer_id VARCHAR(64) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',  -- active | resolved | escalated
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 消息表
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    role VARCHAR(20) NOT NULL,  -- user | assistant | system | human_agent
    content TEXT NOT NULL,
    agent_name VARCHAR(50),
    tools_called JSONB,
    token_usage JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 工单表
CREATE TABLE tickets (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    type VARCHAR(20) NOT NULL,  -- technical | billing | refund
    status VARCHAR(20) DEFAULT 'open',
    priority VARCHAR(10) DEFAULT 'medium',
    assigned_to VARCHAR(64),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 5.3 Chroma — 向量知识库

```
Collection: knowledge_base
  - 文档分块 (chunk_size=500, overlap=50)
  - 元数据: source, category, updated_at
```

## 6. 服务层设计

### 6.1 LLM Provider（多模型服务）

```python
class LLMProvider:
    """统一的LLM调用接口，支持多模型切换"""

    def get_llm(self, model_name: str) -> BaseChatModel:
        ...

    def route_by_complexity(self, query: str) -> str:
        """根据查询复杂度选择模型"""
        ...
```

支持的模型：
- OpenAI: gpt-4o, gpt-4o-mini
- Anthropic: claude-3.5-sonnet, claude-3.5-haiku
- 本地模型: 通过Ollama/vLLM接入

### 6.2 Memory Service（记忆服务）

**短期记忆**（Redis）：
- 当前会话上下文
- 最近N轮对话消息

**长期记忆**（PostgreSQL）：
- 客户历史会话摘要
- 客户偏好记录
- 历史工单信息

### 6.3 Observability Service（可观测性服务）

追踪内容：
- 每次LLM调用：模型、token数、延迟
- 每次工具调用：工具名、输入、输出、延迟
- 路由决策：意图、置信度、理由
- 端到端延迟：从用户请求到最终响应

## 7. 安全设计

| 安全措施 | 实现方式 |
|----------|----------|
| API认证 | JWT Token |
| PII脱敏 | 正则匹配 + LLM辅助识别，在日志中自动mask |
| 输入校验 | Pydantic模型严格校验 |
| 输出过滤 | 内容安全检查，防止敏感信息泄露 |
| 速率限制 | Redis实现，按用户/IP限流 |
| 高风险操作审批 | Human-in-the-loop，退款等操作需人工确认 |

## 8. 技术栈汇总

| 层级 | 技术 | 用途 |
|------|------|------|
| Agent框架 | LangGraph | 多Agent编排、持久化执行、检查点 |
| 后端框架 | FastAPI | REST API + WebSocket |
| 会话状态 | Redis | 高性能状态存储 |
| 持久存储 | PostgreSQL | 会话、消息、工单 |
| 向量库 | Chroma | 知识库语义检索 |
| LLM | OpenAI / Anthropic / 本地 | 多模型支持 |
| 前端 | React + TypeScript | 用户界面 |
| 可观测性 | 自建Tracing + structlog | 执行追踪 |
