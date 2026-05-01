# SmartCS - 开发规范

## 1. Git 提交规范

本项目严格遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范。

### 1.1 Commit Message 格式

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### 1.2 Type 类型

| Type | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(router): add intent classification agent` |
| `fix` | Bug修复 | `fix(refund): correct eligibility check logic` |
| `refactor` | 代码重构 | `refactor(memory): extract redis client to service` |
| `build` | 构建系统变更 | `build: add langgraph dependency` |
| `chore` | 维护任务 | `chore: update .gitignore` |
| `docs` | 文档变更 | `docs: add API documentation` |
| `test` | 测试相关 | `test(router): add unit tests for intent classification` |

### 1.3 Scope 范围（可选）

常用 scope：
- `router` — 路由Agent
- `billing` — 账单Agent
- `technical` — 技术Agent
- `refund` — 退款Agent
- `api` — API层
- `workflow` — LangGraph工作流
- `memory` — 记忆服务
- `knowledge` — 知识库
- `frontend` — 前端
- `config` — 配置

### 1.4 规则

- **所有 commit message 必须使用英文**
- subject 不超过 100 个字符
- subject 不以大写字母开头
- subject 不以句号结尾
- body 和 footer 是可选的

### 1.5 示例

```
feat(router): add intent classification with confidence scoring

- Implement RouterAgent using LangGraph
- Classify intents into billing, technical, refund, general
- Return confidence score for routing decisions
- Low confidence triggers human escalation

Closes #12
```

```
fix(refund): prevent duplicate refund processing

Added idempotency check to process_refund tool to prevent
the same refund from being processed multiple times.

Fixes #45
```

## 2. 分支策略

```
main          ← 生产分支，只接受PR合并
  └── develop ← 开发分支，日常开发基于此分支
       ├── feat/xxx   ← 功能分支
       ├── fix/xxx    ← 修复分支
       └── refactor/xxx ← 重构分支
```

### 分支命名规范

```
feat/add-router-agent
fix/refund-eligibility-check
refactor/extract-llm-provider
docs/update-api-docs
```

## 3. Python 代码规范

### 3.1 工具链

| 工具 | 用途 | 命令 |
|------|------|------|
| uv | 包管理 | `uv sync` / `uv add <pkg>` / `uv run <cmd>` |
| Ruff | Linting + Formatting | `uv run ruff check .` / `uv run ruff format .` |
| mypy | 类型检查 | `uv run mypy backend/` |
| pytest | 测试 | `uv run pytest` |

### 3.2 代码风格

- **Python 版本**: 3.11+
- **行宽**: 100 字符
- **引号**: 双引号
- **导入排序**: Ruff 自动处理
- **类型注解**: 所有函数签名必须有类型注解

### 3.3 命名规范

```python
# 模块/文件名: snake_case
router_agent.py
billing_tools.py

# 类名: PascalCase
class RouterAgent:
class BillingTools:

# 函数/方法: snake_case
def classify_intent():
def get_invoice():

# 常量: UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3
DEFAULT_MODEL = "gpt-4o-mini"

# 私有方法/属性: 前缀下划线
def _internal_method():
self._private_var: str
```

### 3.4 Pydantic 模型规范

```python
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    """聊天请求模型"""

    customer_id: str = Field(..., description="客户ID")
    message: str = Field(..., min_length=1, max_length=5000, description="用户消息")
    conversation_id: str | None = Field(None, description="会话ID，不传则创建新会话")
    stream: bool = Field(False, description="是否流式返回")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "customer_id": "C001",
                    "message": "我想查询上个月的账单",
                    "stream": False
                }
            ]
        }
    }
```

### 3.5 Agent 代码结构

每个 Agent 应遵循以下结构：

```python
# backend/app/agents/billing/agent.py

from langchain_core.messages import BaseMessage
from app.agents.base import BaseAgent
from app.workflows.state import CustomerServiceState

class BillingAgent(BaseAgent):
    """账单Agent - 处理账单相关查询"""

    name = "billing"
    description = "处理发票查询、支付历史、账单问题"

    def __init__(self):
        super().__init__(
            model_name="gpt-4o",
            temperature=0.3,
        )

    async def run(self, state: CustomerServiceState) -> CustomerServiceState:
        """执行Agent逻辑"""
        ...

    def _get_tools(self) -> list:
        """返回该Agent可用的工具列表"""
        return [invoice_lookup, payment_history, billing_summary]

    def _get_system_prompt(self) -> str:
        """返回系统提示词"""
        return "你是一个专业的账单客服Agent..."
```

## 4. 前端代码规范

### 4.1 工具链

| 工具 | 用途 | 命令 |
|------|------|------|
| ESLint | 代码检查 | `npm run lint` |
| Prettier | 代码格式化 | `npm run format` |
| TypeScript | 类型检查 | `npm run typecheck` |

### 4.2 组件规范

```typescript
// 组件文件: PascalCase
// ChatWindow.tsx

interface ChatWindowProps {
  conversationId: string;
  onMessageSent?: (message: string) => void;
}

export function ChatWindow({ conversationId, onMessageSent }: ChatWindowProps) {
  // hooks 在最前面
  const [messages, setMessages] = useState<Message[]>([]);
  const { sendMessage, isLoading } = useChat(conversationId);

  // 事件处理函数
  const handleSubmit = async (content: string) => {
    await sendMessage(content);
    onMessageSent?.(content);
  };

  // 渲染
  return (
    <div className="flex flex-col h-full">
      {/* ... */}
    </div>
  );
}
```

## 5. 测试规范

### 5.1 测试类型

| 类型 | 目录 | 覆盖率目标 | 说明 |
|------|------|-----------|------|
| 单元测试 | `tests/unit/` | 80%+ | Agent逻辑、工具函数 |
| 集成测试 | `tests/integration/` | 核心流程 | API端点、Agent协作 |
| E2E测试 | `tests/e2e/` | 关键路径 | 完整用户流程 |

### 5.2 测试命名

```python
class TestRouterAgent:
    def test_classify_billing_intent(self):
        """测试：正确分类账单相关意图"""
        ...

    def test_low_confidence_triggers_escalation(self):
        """测试：低置信度触发人工升级"""
        ...

    def test_handles_empty_message(self):
        """测试：处理空消息"""
        ...
```

### 5.3 Mock 策略

```python
# Mock LLM调用，避免测试时消耗token
@pytest.fixture
def mock_llm(monkeypatch):
    mock = AsyncMock()
    mock.ainvoke.return_value = AIMessage(content="mocked response")
    monkeypatch.setattr("app.services.llm.provider.get_llm", lambda *args: mock)
    return mock
```

## 6. 文档规范

| 文档 | 更新时机 |
|------|----------|
| `docs/requirements.md` | 需求变更时 |
| `docs/architecture.md` | 架构决策变更时 |
| `docs/api.md` | API变更时 |
| `docs/CHANGELOG.md` | 每次发版时 |
| 代码注释 | 复杂逻辑必须注释，简单代码不加注释 |
| Docstring | 所有公开类和函数 |
