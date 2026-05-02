# AGENTS.md - SmartCS 开发指南

## 项目架构

- **Backend**: FastAPI + LangGraph 多Agent系统，入口 `backend/app/main.py`
- **Frontend**: React 19 + Vite + TypeScript，入口 `frontend/src/`
- **Agent路由**: Router → Billing/Technical/Refund/General，单一入口 `backend/app/workflows/customer_service.py`
- **HITL规则**: 退款金额 ≥ ¥500 时进入人工审批队列

## 常用命令

```bash
# 后端启动（开发）
uv run uvicorn backend.app.main:app --reload --port 8000
# 或
uv run python backend/scripts/run_server.py

# 前端启动
cd frontend && npm run dev

# 测试
uv run pytest backend/tests/ -v
uv run pytest backend/tests/unit/test_xxx.py -v

# Lint & Format（先 lint 再 format）
uv run ruff check .
uv run ruff format .

# 类型检查
uv run mypy backend/

# 基础设施（PostgreSQL + Redis）
docker-compose up -d
```

## 工具链

| 工具 | 用途 |
|------|------|
| `uv` | Python包管理（sync/add/run） |
| `ruff` | Lint + Format，行宽100 |
| `mypy` | 类型检查，Python 3.11 |
| `pre-commit` | 钩子：conventional-commit + ruff + mypy |

## 规范

- **Commit**: Conventional Commits，`feat|fix|refactor|build|chore|docs|test(scope): description`
- **Python**: 双引号，类型注解必须
- **前端**: `npm run lint` / `npm run typecheck`

## 环境变量

必须设置 `.env`（复制 `.env.example`）：
- `DATABASE_URL`: PostgreSQL连接
- `REDIS_URL`: Redis连接
- `MINIMAX_API_KEY`: MiniMax LLM密钥（项目使用MiniMax而非OpenAI）
- `LLM_PROVIDER`: `minimax`（默认）

## 数据库

- 迁移: `alembic upgrade head`
- 种子数据: `uv run python backend/scripts/seed_data.py`
- 创建用户: `uv run python backend/scripts/create_users.py`

## 注意事项

- MiniMax API 在 Router Agent 中存在不稳定性，参考 README.md "Current Status"
- Chroma 向量库数据在 `chroma_db/` 目录，docker-compose 中挂载为 volume
- pre-commit 会在 commit 时自动运行 lint 和 mypy
