# SmartCS - Enterprise Multi-Agent Customer Service System

A production-ready multi-agent customer service system built with **LangGraph** + **FastAPI** + **React**, powered by **DeepSeek** LLM.

## Architecture Overview

```
User Request
    │
    ▼
┌─────────────────────────────────────────────┐
│            FastAPI + WebSocket               │
│         (Real-time bidirectional)            │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│           LangGraph StateGraph              │
│  ┌─────────────────────────────────────┐   │
│  │         Router Agent                │   │
│  │   (Keyword + LLM dual strategy)     │   │
│  └──────────┬──────────────────────────┘   │
│             │                              │
│    ┌────────┼────────┬────────────┐        │
│    ▼        ▼        ▼            ▼        │
│ Billing  Technical  Refund    General      │
│ Agent    Agent      Agent     Agent        │
│    │        │        │            │        │
│    └────────┴────────┴────────────┘        │
│             │                              │
│             ▼                              │
│      HITL Approval Check                   │
│   (Refund ≥ ¥500 requires human)          │
└─────────────────────────────────────────────┘
                   │
                   ▼
           DeepSeek LLM
```

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── agents/           # Multi-agent definitions
│   │   │   ├── base.py       # BaseAgent ABC
│   │   │   ├── router/       # Intent classification agent
│   │   │   ├── billing/      # Billing specialist
│   │   │   ├── technical/    # Technical support specialist
│   │   │   ├── refund/       # Refund processing specialist
│   │   │   └── general/      # General FAQ specialist
│   │   ├── tools/            # 13 LangChain tools
│   │   │   ├── billing/      # invoice, payment, summary
│   │   │   ├── technical/    # knowledge, tickets, product
│   │   │   ├── refund/       # order, eligibility, process
│   │   │   └── general/      # FAQ, company info
│   │   ├── workflows/        # LangGraph StateGraph
│   │   │   ├── state.py      # CustomerServiceState
│   │   │   └── customer_service.py  # Workflow orchestration
│   │   ├── services/
│   │   │   ├── llm/          # Multi-provider LLM (MiniMax/OpenAI/Anthropic)
│   │   │   ├── memory/       # Redis/In-memory short-term store
│   │   │   ├── redis/        # Redis client and session management
│   │   │   ├── knowledge/    # Chroma vector DB for knowledge base
│   │   │   ├── observability/ # Trace context
│   │   │   ├── orchestrator.py
│   │   │   └── approval_queue.py
│   │   ├── repositories/     # Database repositories
│   │   │   ├── base.py       # BaseRepository with CRUD
│   │   │   ├── conversation.py # Conversation & Message repos
│   │   │   └── approval.py   # Approval repository
│   │   ├── api/
│   │   │   ├── v1/           # REST endpoints
│   │   │   │   ├── auth.py   # JWT authentication
│   │   │   │   ├── chat.py   # Chat with SSE streaming
│   │   │   │   ├── admin.py  # Approval management
│   │   │   │   ├── health.py # Health & debug endpoints
│   │   │   │   └── traces.py # Trace API
│   │   │   └── websocket/    # WebSocket real-time chat
│   │   ├── core/
│   │   │   ├── config/       # Pydantic Settings
│   │   │   ├── database.py   # SQLAlchemy async engine
│   │   │   └── security/     # JWT token handling
│   │   ├── models/
│   │   │   ├── schemas/      # Pydantic models
│   │   │   └── db/           # SQLAlchemy ORM models
│   │   └── main.py           # FastAPI app entry
│   ├── tests/
│   │   ├── unit/             # 28 unit tests
│   │   └── integration/      # Integration tests
│   ├── alembic/              # DB migrations
│   └── scripts/              # Dev & debug scripts
├── frontend/
│   ├── src/
│   │   ├── components/chat/  # ChatWindow, MessageBubble
│   │   ├── pages/            # Chat, Admin, Dashboard
│   │   ├── hooks/            # useWebSocket (auto-reconnect)
│   │   ├── store/            # Zustand state management
│   │   └── services/         # REST API client
│   ├── package.json
│   ├── vite.config.ts
│   ├── Dockerfile            # Frontend container
│   └── nginx.conf            # Nginx configuration
├── docs/                     # Project documentation (Chinese)
│   ├── architecture.md       # System architecture
│   ├── requirements.md       # 21 FRs + 7 NFRs
│   ├── api.md                # API reference
│   ├── deployment.md         # Deployment guide
│   ├── development.md        # Dev standards
│   └── CHANGELOG.md          # Version history
├── Dockerfile                # Backend container
├── docker-compose.yml        # Full stack deployment
├── alembic.ini               # Alembic configuration
└── .env                      # Environment config
```

## Features

### Multi-Agent System
- **Router Agent**: Dual-strategy classification (keyword + LLM), handles Chinese/English intent values
- **Billing Agent**: Invoice lookup, payment history, billing summary
- **Technical Agent**: Knowledge search, ticket create/lookup, product info
- **Refund Agent**: Order lookup, refund eligibility check, process refund
- **General Agent**: FAQ search, company info

### Human-in-the-Loop (HITL)
- Refund operations ≥ ¥500 require human approval
- Admin API for approval queue management
- Human takeover / release capabilities

### Real-time Communication
- WebSocket-based bidirectional chat
- SSE streaming responses for better UX
- Auto-reconnect with exponential backoff
- Event streaming (typing, agent selection, tool calls)

### Data Persistence
- PostgreSQL for conversations, messages, and approvals
- Redis for session management and caching
- Chroma vector DB for knowledge base semantic search
- SQLAlchemy async ORM with repository pattern

### Authentication & Security
- JWT-based authentication
- User registration and login
- Role-based access control (admin, agent, viewer)
- Password hashing with bcrypt

### Observability
- In-memory trace context with span tracking
- Trace API endpoint for debugging
- Per-request conversation tracing

### Deployment
- Docker containers for backend and frontend
- Docker Compose for full stack deployment
- Nginx reverse proxy for frontend
- Health checks and service dependencies

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- MiniMax API key ([Get one here](https://platform.minimaxi.com/))

### 1. Clone & Configure

```bash
git clone <repo-url>
cd smartcs
cp .env.example .env
# Edit .env with your MiniMax API key
```

### 2. Backend Setup

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and create virtual environment
uv sync

# Run backend
uv run uvicorn backend.app.main:app --reload --port 8000
# Or: uv run python backend/scripts/run_server.py
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

### 4. Infrastructure (Optional)

```bash
# Start Redis + PostgreSQL
docker-compose up -d
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider (`minimax`/`openai`/`anthropic`/`deepseek`) | `deepseek` |
| `MINIMAX_API_KEY` | MiniMax API key | - |
| `DEFAULT_MODEL` | Default model for all agents | `MiniMax-M2.7` |
| `ROUTER_MODEL` | Router agent model | `MiniMax-M2.7` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `DATABASE_URL` | PostgreSQL connection string | - |
| `APP_ENV` | Environment (`development`/`production`) | `development` |
| `DEBUG` | Enable debug logging | `false` |

### Available MiniMax Models

| Model | Speed | Quality |
|-------|-------|---------|
| `MiniMax-M2.7` | Medium | Highest |
| `MiniMax-M2.7-highspeed` | Fast | High |
| `MiniMax-M2.5` | Medium | High |
| `MiniMax-M2.5-highspeed` | Fast | Medium |
| `MiniMax-M2.1` | Medium | Medium |
| `MiniMax-M2.1-highspeed` | Fast | Lower |
| `MiniMax-M2` | Slow | Lower |

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login (OAuth2 password flow)
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user info

### Chat
- `POST /api/v1/chat` - Send message (REST)
- `POST /api/v1/chat/stream` - Send message (SSE streaming)
- `WS /ws/chat/{conversation_id}` - Real-time chat (WebSocket)

### Admin
- `GET /api/v1/admin/approvals` - List pending approvals
- `POST /api/v1/admin/approvals/{id}/decide` - Approve/Reject
- `POST /api/v1/admin/conversations/{id}/takeover` - Human takeover
- `POST /api/v1/admin/conversations/{id}/release` - Release to AI

### System
- `GET /api/v1/health` - Health check
- `GET /api/v1/debug/config` - Current configuration
- `GET /api/v1/traces/{trace_id}` - Request trace

## Docker Deployment

### Full Stack Deployment

```bash
# Set your MiniMax API key
export MINIMAX_API_KEY=your_api_key_here

# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Services
- **Frontend**: http://localhost:80
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Individual Container Build

```bash
# Backend only
docker build -t smartcs-backend .
docker run -p 8000:8000 smartcs-backend

# Frontend only
docker build -t smartcs-frontend -f frontend/Dockerfile .
docker run -p 80:80 smartcs-frontend
```

## Testing

```bash
# Run all tests
uv run pytest backend/tests/ -v

# Run specific test file
uv run pytest backend/tests/unit/test_tools.py -v

# With coverage
uv run pytest backend/tests/ --cov=backend/app --cov-report=html

# Linting
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy backend/
```

## Current Status

### ✅ Completed
- [x] Multi-agent LangGraph architecture
- [x] Router Agent with keyword + LLM dual strategy
- [x] 4 specialist agents with 13 tools
- [x] HITL approval queue
- [x] WebSocket real-time chat
- [x] SSE streaming responses
- [x] MiniMax LLM integration
- [x] React frontend (Chat, Admin, Dashboard)
- [x] PostgreSQL database integration
- [x] Redis session and cache management
- [x] Chroma vector DB for knowledge base
- [x] JWT authentication system
- [x] Docker containerization
- [x] Integration tests
- [x] Unit tests (28 passing)
- [x] Project documentation (architecture, API, requirements)

### 🚧 In Progress
- [ ] Frontend dark theme refinements

### 📋 Planned
- [ ] Rate limiting
- [ ] PII detection & redaction
- [ ] E2E tests
- [ ] CI/CD pipeline

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11+, FastAPI, LangGraph, LangChain |
| **Frontend** | React 19, TypeScript, Vite 6, Tailwind CSS, Zustand |
| **LLM** | MiniMax (OpenAI-compatible API) |
| **Database** | PostgreSQL 15, SQLAlchemy async ORM |
| **Cache** | Redis 7 |
| **Vector DB** | Chroma |
| **Auth** | JWT, bcrypt |
| **Testing** | pytest, 28 unit tests, integration tests |
| **Deployment** | Docker, Docker Compose, Nginx |
| **Docs** | Chinese (docs/), English (README, code comments) |

## Git Convention

This project enforces [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

# Examples:
feat(router): add keyword-based fallback classification
fix(llm): handle Chinese intent values from MiniMax
test(tools): add unit tests for billing tools
docs: update CHANGELOG with v0.2.0 changes
```

**Types**: `feat`, `fix`, `refactor`, `build`, `chore`, `docs`, `test`

## License

This project is for educational and development purposes.
