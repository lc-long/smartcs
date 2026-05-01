# SmartCS - API 文档

## 1. 概述

SmartCS API 采用 RESTful 风格，所有接口返回 JSON 格式。实时对话使用 WebSocket。

**Base URL**: `http://localhost:8000/api/v1`

**认证方式**: Bearer Token (JWT)

```
Authorization: Bearer <token>
```

## 2. 对话接口

### 2.1 发送消息

```
POST /api/v1/chat
```

**请求体**:
```json
{
    "conversation_id": "uuid (可选，不传则创建新会话)",
    "customer_id": "string (必填)",
    "message": "string (必填)",
    "stream": false
}
```

**响应** (非流式):
```json
{
    "conversation_id": "uuid",
    "message": {
        "role": "assistant",
        "content": "您好！我来帮您查询账单信息。请问您想查询哪个月份的账单？",
        "agent_name": "billing",
        "tools_called": [],
        "created_at": "2025-01-01T00:00:00Z"
    },
    "metadata": {
        "intent": "billing",
        "confidence": 0.92,
        "routing_reasoning": "用户提到了'账单'关键词",
        "model_used": "gpt-4o-mini",
        "token_usage": {
            "prompt_tokens": 150,
            "completion_tokens": 30,
            "total_tokens": 180
        },
        "latency_ms": 1200
    }
}
```

**响应** (流式):
```
Content-Type: text/event-stream

data: {"type": "token", "content": "您"}
data: {"type": "token", "content": "好"}
data: {"type": "token", "content": "！"}
data: {"type": "metadata", "intent": "billing", "confidence": 0.92}
data: {"type": "done"}
```

### 2.2 WebSocket 实时对话

```
WS /ws/chat/{conversation_id}
```

**客户端发送**:
```json
{
    "type": "message",
    "content": "我想退款"
}
```

**服务端推送**:
```json
// Agent开始处理
{"type": "agent_start", "agent": "router"}

// 路由决策
{"type": "route_decision", "intent": "refund", "confidence": 0.95}

// Agent切换
{"type": "agent_switch", "from": "router", "to": "refund"}

// 流式token
{"type": "token", "content": "好"}

// 工具调用
{"type": "tool_call", "tool": "order_lookup", "args": {"order_id": "123"}}

// 工具结果
{"type": "tool_result", "tool": "order_lookup", "result": {...}}

// 人工介入请求
{"type": "human_approval_needed", "reason": "退款金额超过500元", "context": {...}}

// 完成
{"type": "done", "metadata": {...}}
```

## 3. 会话管理接口

### 3.1 获取会话列表

```
GET /api/v1/conversations?customer_id=xxx&status=active&limit=20&offset=0
```

**响应**:
```json
{
    "items": [
        {
            "id": "uuid",
            "customer_id": "string",
            "status": "active",
            "last_message": "我想查询账单",
            "last_agent": "billing",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:05:00Z"
        }
    ],
    "total": 50,
    "limit": 20,
    "offset": 0
}
```

### 3.2 获取会话详情

```
GET /api/v1/conversations/{conversation_id}
```

**响应**:
```json
{
    "id": "uuid",
    "customer_id": "string",
    "status": "active",
    "messages": [
        {
            "id": "uuid",
            "role": "user",
            "content": "我想退款",
            "created_at": "2025-01-01T00:00:00Z"
        },
        {
            "id": "uuid",
            "role": "assistant",
            "content": "好的，请提供您的订单号",
            "agent_name": "refund",
            "tools_called": ["order_lookup"],
            "created_at": "2025-01-01T00:00:01Z"
        }
    ],
    "metadata": {
        "total_tokens": 1500,
        "total_cost": 0.003,
        "resolution_status": "in_progress"
    }
}
```

### 3.3 人工接管

```
POST /api/v1/conversations/{conversation_id}/takeover
```

**请求体**:
```json
{
    "agent_id": "human_agent_001",
    "reason": "客户情绪激动，需要人工安抚"
}
```

**响应**:
```json
{
    "success": true,
    "message": "已接管会话",
    "conversation_status": "human_handling"
}
```

### 3.4 释放会话（交还AI）

```
POST /api/v1/conversations/{conversation_id}/release
```

**响应**:
```json
{
    "success": true,
    "message": "会话已交还AI处理"
}
```

## 4. 管理接口

### 4.1 知识库管理

**上传文档**:
```
POST /api/v1/admin/knowledge/upload
Content-Type: multipart/form-data

file: <file>
category: "product_docs" | "faq" | "policy"
```

**查询知识库**:
```
GET /api/v1/admin/knowledge?category=faq&limit=20
```

**删除文档**:
```
DELETE /api/v1/admin/knowledge/{document_id}
```

### 4.2 Agent配置

**获取Agent配置**:
```
GET /api/v1/admin/agents
```

**响应**:
```json
{
    "agents": [
        {
            "name": "router",
            "model": "gpt-4o-mini",
            "enabled": true,
            "config": {
                "temperature": 0.0,
                "max_tokens": 500
            }
        },
        {
            "name": "billing",
            "model": "gpt-4o",
            "enabled": true,
            "config": {
                "temperature": 0.3,
                "max_tokens": 1000
            }
        }
    ]
}
```

**更新Agent配置**:
```
PATCH /api/v1/admin/agents/{agent_name}
```

```json
{
    "model": "claude-3.5-sonnet",
    "config": {
        "temperature": 0.5
    }
}
```

### 4.3 人工审批队列

**获取待审批列表**:
```
GET /api/v1/admin/approvals?status=pending
```

**响应**:
```json
{
    "items": [
        {
            "id": "uuid",
            "conversation_id": "uuid",
            "type": "refund_approval",
            "amount": 800.00,
            "reason": "商品质量问题",
            "customer_id": "C001",
            "created_at": "2025-01-01T00:00:00Z",
            "context": {
                "order_id": "ORD123",
                "product": "Smart Watch Pro",
                "purchase_date": "2024-12-15"
            }
        }
    ],
    "total": 5
}
```

**审批操作**:
```
POST /api/v1/admin/approvals/{approval_id}
```

```json
{
    "decision": "approve" | "reject",
    "comment": "同意退款，商品确有质量问题"
}
```

## 5. 数据看板接口

### 5.1 概览指标

```
GET /api/v1/dashboard/overview?period=7d
```

**响应**:
```json
{
    "period": "7d",
    "total_conversations": 1250,
    "resolved_by_ai": 875,
    "escalated_to_human": 375,
    "resolution_rate": 0.70,
    "avg_response_time_ms": 2300,
    "avg_conversation_turns": 4.2,
    "total_tokens_used": 500000,
    "estimated_cost": 12.50
}
```

### 5.2 Agent性能

```
GET /api/v1/dashboard/agents?period=7d
```

**响应**:
```json
{
    "agents": [
        {
            "name": "billing",
            "total_calls": 450,
            "avg_latency_ms": 1800,
            "success_rate": 0.95,
            "avg_tokens": 320,
            "top_tools": [
                {"tool": "invoice_lookup", "calls": 380},
                {"tool": "payment_history", "calls": 200}
            ]
        }
    ]
}
```

### 5.3 意图分布

```
GET /api/v1/dashboard/intents?period=7d
```

**响应**:
```json
{
    "distribution": [
        {"intent": "billing", "count": 450, "percentage": 0.36},
        {"intent": "technical", "count": 350, "percentage": 0.28},
        {"intent": "refund", "count": 200, "percentage": 0.16},
        {"intent": "general", "count": 250, "percentage": 0.20}
    ]
}
```

## 6. 健康检查

```
GET /api/v1/health
```

**响应**:
```json
{
    "status": "healthy",
    "version": "0.1.0",
    "services": {
        "redis": "connected",
        "postgresql": "connected",
        "chroma": "connected",
        "llm_openai": "available",
        "llm_anthropic": "available"
    },
    "uptime_seconds": 86400
}
```

## 7. 错误响应格式

```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "customer_id is required",
        "details": {
            "field": "customer_id",
            "type": "missing"
        }
    }
}
```

**错误码**:
| HTTP状态码 | 错误码 | 说明 |
|-----------|--------|------|
| 400 | VALIDATION_ERROR | 请求参数校验失败 |
| 401 | UNAUTHORIZED | 未认证 |
| 403 | FORBIDDEN | 无权限 |
| 404 | NOT_FOUND | 资源不存在 |
| 429 | RATE_LIMITED | 请求频率超限 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |
| 502 | LLM_ERROR | LLM调用失败 |
| 503 | SERVICE_UNAVAILABLE | 服务不可用 |
