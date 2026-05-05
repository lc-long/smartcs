# 智能客服架构重构计划

## 背景

将现有的多Agent架构（Router + Supervisor + Billing/Technical/Refund/General）简化为**单一Agent架构**。

### 原因
1. 电商客服场景任务复杂度可控，单Agent配齐工具即可处理
2. 多Agent带来的跨Agent通信、工具重复、调试复杂等问题大于其价值
3. Supervisor实际未正常工作（bug：调用不存在的self.llm）
4. General Agent工具过多（17个），说明分工不明确

### 目标
- 单一Agent处理所有客服场景
- 工具按功能分组统一管理，不重复
- 架构简化，调试容易
- 保留HITL安全机制

---

## 当前架构

```
用户 → Router → Supervisor → Billing/Technical/Refund/General → Supervisor汇总 → 用户
```

问题：
- 工具重复（order_lookup在General和Refund都有）
- 层级过多，响应慢
- Supervisor有bug未修复
- Agent间通信复杂

---

## 目标架构

```
用户 → 单Agent（整合所有工具） → HITL检查 → 用户
```

### 单Agent职责
- 理解用户意图
- 选择正确工具
- 处理订单/退款/账单/技术/产品查询等所有场景
- 高风险操作（退款≥¥2000）触发HITL审批

---

## 实施计划

### Phase 1: 创建新架构文件

#### 1.1 创建统一工具文件 `backend/app/tools/unified.py`
整合所有工具到单一文件：
- ecommerce: create_order, cancel_order, get_customer_address, search_products, get_product_info
- refund: order_lookup, refund_eligibility, process_refund, refund_status_lookup
- billing: invoice_lookup, payment_history, billing_summary, order_payment_match
- technical: knowledge_search, ticket_create, ticket_lookup, ticket_update, product_info
- general: faq_search, company_info, customer_info, shipment_tracking
- advanced: loyalty_points_lookup, customer_coupon_lookup, product_recommendation, product_review_lookup, customer_feedback_lookup, customer_feedback_submit, loyalty_points_redeem, coupon_apply

#### 1.2 创建新的单Agent `backend/app/agents/service_agent.py`
- 整合所有工具
- 清晰的system prompt指导意图识别和工具选择
- 支持多轮对话和上下文理解

#### 1.3 创建简化的Workflow `backend/app/workflows/service_workflow.py`
- 接收用户消息
- 调用单Agent处理
- HITL检查（针对高风险操作）
- 返回结果

---

### Phase 2: 修改入口文件

#### 2.1 修改 `backend/app/main.py`
- 更新API路由，使用新的service_workflow
- 保持WebSocket端点不变

#### 2.2 修改 `backend/app/api/v1/chat.py` 或相关入口
- 调用新的service_workflow

---

### Phase 3: 清理旧文件

#### 3.1 保留文件
- `backend/app/agents/base.py` - 保留为BaseAgent基类
- `backend/app/agents/general/agent.py` - 重写为单Agent

#### 3.2 删除文件（不再需要）
- `backend/app/agents/router/` - Router Agent
- `backend/app/agents/supervisor/` - Supervisor Agent
- `backend/app/agents/billing/` - Billing Agent
- `backend/app/agents/technical/` - Technical Agent
- `backend/app/agents/refund/` - Refund Agent
- `backend/app/workflows/customer_service.py` - 旧的复杂workflow

#### 3.3 删除工具目录
- `backend/app/tools/billing/` → 合并到 unified.py
- `backend/app/tools/technical/` → 合并到 unified.py
- `backend/app/tools/refund/` → 合并到 unified.py
- `backend/app/tools/general/` → 合并到 unified.py
- `backend/app/tools/advanced/` → 合并到 unified.py

---

### Phase 4: 更新前端

#### 4.1 确认前端不需要大改
- ChatWindow.tsx 已经可以正常工作
- WebSocket处理不需要改变
- 只需要确认消息格式兼容

---

### Phase 5: 测试

#### 5.1 运行现有测试
```bash
uv run pytest backend/tests/ -v
```

#### 5.2 手动测试场景
- 查订单
- 取消订单
- 申请退款
- 查产品
- 账单核对
- 技术工单

---

## 文件变更清单

### 新建
- `backend/app/agents/service_agent.py` - 单Agent
- `backend/app/workflows/service_workflow.py` - 简化workflow
- `backend/app/tools/unified.py` - 统一工具

### 修改
- `backend/app/main.py` - 更新路由
- `backend/app/agents/base.py` - 可能需要简化
- `backend/app/agents/general/agent.py` - 重写为单Agent

### 删除
- `backend/app/agents/router/` - 整个目录
- `backend/app/agents/supervisor/` - 整个目录
- `backend/app/agents/billing/` - 整个目录
- `backend/app/agents/technical/` - 整个目录
- `backend/app/agents/refund/` - 整个目录
- `backend/app/workflows/customer_service.py`
- `backend/app/tools/billing/`
- `backend/app/tools/technical/`
- `backend/app/tools/refund/`
- `backend/app/tools/general/`
- `backend/app/tools/advanced/`

---

## 风险与缓解

### 风险1: 单一Agent处理复杂任务失败
**缓解**: 工具设计为可组合，单Agent可以连续调用多个工具

### 风险2: 意图识别不准确
**缓解**: system prompt足够详细，包含意图关键词和工具映射

### 风险3: 改动太大难以回滚
**缓解**: 先提交当前代码为备份commit，不删除旧文件直到新架构验证通过

---

## 进度追踪

- [ ] Phase 1: 创建新架构文件
- [ ] Phase 2: 修改入口文件
- [ ] Phase 3: 清理旧文件
- [ ] Phase 4: 更新前端
- [ ] Phase 5: 测试验证

---

## 预期结果

1. 代码量减少（删除重复工具和Agent）
2. 架构清晰单一
3. 调试简单
4. 响应速度提升