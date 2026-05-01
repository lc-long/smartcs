# SmartCS - 部署文档

## 1. 环境要求

| 组件 | 版本要求 |
|------|----------|
| Python | >= 3.11 |
| Node.js | >= 18 |
| Redis | >= 7.0 |
| PostgreSQL | >= 15 |
| Docker (可选) | >= 24.0 |

## 2. 快速启动（开发环境）

### 2.1 克隆项目

```bash
git clone <repo-url>
cd agents
```

### 2.2 启动基础设施

```bash
# 使用 Docker Compose 启动 Redis 和 PostgreSQL
docker-compose up -d
```

### 2.3 后端设置

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -e ".[dev]"

# 复制环境变量
cp .env.example .env
# 编辑 .env 填入 API Keys

# 初始化数据库
alembic upgrade head

# 启动后端
uvicorn backend.app.main:app --reload --port 8000
```

### 2.4 前端设置

```bash
cd frontend
npm install
npm run dev
```

前端访问: `http://localhost:3000`
后端API文档: `http://localhost:8000/docs`

## 3. 环境变量配置

### `.env.example`

```bash
# ===== Application =====
APP_NAME=SmartCS
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO

# ===== API Server =====
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=["http://localhost:3000"]

# ===== Database =====
DATABASE_URL=postgresql+asyncpg://smartcs:smartcs@localhost:5432/smartcs

# ===== Redis =====
REDIS_URL=redis://localhost:6379/0

# ===== LLM API Keys =====
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1
ANTHROPIC_API_KEY=sk-ant-xxx

# ===== Model Configuration =====
DEFAULT_MODEL=gpt-4o-mini
ROUTER_MODEL=gpt-4o-mini
BILLING_MODEL=gpt-4o
TECHNICAL_MODEL=gpt-4o
REFUND_MODEL=gpt-4o
GENERAL_MODEL=gpt-4o-mini

# ===== Vector Database =====
CHROMA_PERSIST_DIR=./chroma_db
CHROMA_COLLECTION=knowledge_base

# ===== Security =====
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# ===== Observability =====
ENABLE_TRACING=true
TRACE_SAMPLE_RATE=1.0
```

## 4. Docker Compose

```yaml
# docker-compose.yml
version: "3.8"

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: smartcs
      POSTGRES_PASSWORD: smartcs
      POSTGRES_DB: smartcs
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - redis
      - postgres
    volumes:
      - ./chroma_db:/app/chroma_db

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://backend:8000

volumes:
  redis_data:
  postgres_data:
```

## 5. 生产部署注意事项

### 5.1 安全

- [ ] 更换 JWT_SECRET_KEY 为强随机字符串
- [ ] 设置 DEBUG=false
- [ ] 配置 HTTPS（Nginx反向代理）
- [ ] 限制 CORS_ORIGINS 为实际域名
- [ ] 数据库使用强密码
- [ ] API Keys 使用环境变量或密钥管理服务

### 5.2 性能

- [ ] Redis 配置持久化（AOF）
- [ ] PostgreSQL 配置连接池
- [ ] 使用 Gunicorn + Uvicorn workers
- [ ] 配置适当的 worker 数量（通常 2*CPU + 1）

### 5.3 可靠性

- [ ] 配置健康检查端点
- [ ] 设置日志收集（ELK/Loki）
- [ ] 配置监控告警
- [ ] 定期备份数据库

### 5.4 Gunicorn 配置

```bash
gunicorn backend.app.main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --keep-alive 5 \
  --access-logfile - \
  --error-logfile -
```

## 6. CI/CD（可选）

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
      - run: ruff check .
      - run: mypy backend/
      - run: pytest --cov=backend
```
