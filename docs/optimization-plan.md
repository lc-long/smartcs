# Agent 优化计划

> 创建时间: 2026-05-03
> 优先级: 高→中→低

## 🔴 高优先级

### 1. HITL 审批流未真正阻塞
**问题**：`hitl_check_node` 创建审批项后立即返回，用户收到"等待审批"消息但工作流继续执行完毕。

**修复方案**：
- 引入 `asyncio.Event` 或 Redis pub/sub 机制
- 审批完成前工作流暂停在 `hitl_check` 节点
- WebSocket 通知客户端显示"等待人工审批"状态
- 审批完成后通过 Redis 事件唤醒工作流

**影响文件**：
- `backend/app/workflows/customer_service.py`
- `backend/app/services/approval_queue.py`
- `backend/app/api/v1/admin.py`

---

### 2. 退款审批逻辑重复
**问题**：`process_refund` 工具自己判断金额决定是否直接批准（≤¥500 直接 approved），与 HITL queue 是两套逻辑。

**修复方案**：
- 工具层 `process_refund` 只记录退款意图，不执行审批
- 所有退款统一经 HITL queue 流转
- HITL 审批通过后才真正执行退款

**影响文件**：
- `backend/app/tools/refund/tools.py`

---

### 3. Redis 异步初始化未调用
**问题**：`ApprovalQueue._async_init()` 定义了但从未调用，pending items 无法从 Redis 恢复。

**修复方案**：
- 在 FastAPI startup 事件中调用 `_async_init()`
- 或在 workflow 首次使用时延迟初始化

**影响文件**：
- `backend/app/services/approval_queue.py`
- `backend/app/main.py`

---

## 🟡 中优先级

### 4. Working Memory 持久化 fire-and-forget
**问题**：Redis 持久化用 `asyncio.create_task` 但不 await，失败静默忽略。

**修复方案**：
- 添加错误处理和重试机制
- 可选：持久化失败时降级到内存

**影响文件**：
- `backend/app/services/memory/working.py`

---

### 5. Router 只用最后一条消息
**问题**：只分析用户最新一条消息，未利用完整对话历史。

**修复方案**：
- 传入最近 N 条对话消息供 Router 参考
- 对话历史作为独立字段传入

**影响文件**：
- `backend/app/agents/router/agent.py`
- `backend/app/workflows/customer_service.py`

---

### 6. 多意图只返回主意图
**问题**：`is_multi_intent=True` 但 `RouteDecision` 只取第一个。

**修复方案**：
- 工作流支持并行调用多个 Agent 节点
- Supervisor 协调多 Agent 结果聚合

**影响文件**：
- `backend/app/workflows/customer_service.py`

---

## 🟢 低优先级

| 问题 | 建议方案 |
|------|---------|
| TokenCounter 进程内独享 | 多 worker 时用 Redis 汇总 |
| 情绪分析仅关键词匹配 | 考虑接入情感分析 API |
| Supervisor 规划失败静默 | 添加 metrics 暴露失败次数 |
| 无 Rate Limiting | 接入 API 限流中间件 |
| 无 PII 检测 | 添加敏感信息脱敏中间件 |

---

## 执行顺序

```
1. Redis 初始化修复（基础设施，可独立进行）✅
2. 退款逻辑统一（改动较小）✅
3. HITL 阻塞流程修复（核心，需仔细设计）✅
4. Working Memory 持久化修复 ✅
5. Router 上下文扩展 ✅
6. 多意图并行支持 ✅
```

---

## 已完成 ✅

| 任务 | 状态 | 提交 |
|------|------|------|
| Redis 初始化修复 | ✅ | caef7bb |
| 退款逻辑统一 | ✅ | d54ba25 |
| HITL 阻塞流程 | ✅ | 14bce3b |
| Working Memory | ✅ | fad2682 |
| Router 上下文 | ✅ | fd5da4f |
| 多意图并行 | ✅ | d0c9ae5 |