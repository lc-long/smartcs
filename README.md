# SmartCS - Enterprise Multi-Agent Customer Service System

A production-ready multi-agent customer service system built with **LangGraph** + **FastAPI** + **React**, powered by **MiniMax** LLM.

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
           MiniMax LLM (M2.7)
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
│   │   │   ├── memory/       # In-memory short-term store
│   │   │   ├── observability/ # Trace context
│   │   │   ├── orchestrator.py
│   │   │   └── approval_queue.py
│   │   ├── api/
│   │   │   ├── v1/           # REST endpoints
│   │   │   └── websocket/    # WebSocket real-time chat
│   │   ├── core/config/      # Pydantic Settings
│   │   ├── models/           # Pydantic schemas
│   │   └── main.py           # FastAPI app entry
│   ├── tests/
│   │   └── unit/             # 28 unit tests
│   ├── alembic/              # DB migrations (TODO)
│   └── scripts/              # Dev & debug scripts
├── frontend/
│   ├── src/
│   │   ├── components/chat/  # ChatWindow, MessageBubble
│   │   ├── pages/            # Chat, Admin, Dashboard
│   │   ├── hooks/            # useWebSocket (auto-reconnect)
│   │   ├── store/            # Zustand state management
│   │   └── services/         # REST API client
│   ├── package.json
│   └── vite.config.ts
├── docs/                     # Project documentation (Chinese)
│   ├── architecture.md       # System architecture
│   ├── requirements.md       # 21 FRs + 7 NFRs
│   ├── api.md                # API reference
│   ├── deployment.md         # Deployment guide
│   ├── development.md        # Dev standards
│   └── CHANGELOG.md          # Version history
├── docker-compose.yml        # Redis + PostgreSQL
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
- Auto-reconnect with exponential backoff
- Event streaming (typing, agent selection, tool calls)

### Observability
- In-memory trace context with span tracking
- Trace API endpoint for debugging
- Per-request conversation tracing

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
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
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Run backend
python backend/scripts/run_server.py
# Or: uvicorn backend.app.main:app --reload --port 8000
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
| `LLM_PROVIDER` | LLM provider (`minimax`/`openai`/`anthropic`) | `minimax` |
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

### Chat
- `POST /api/v1/chat` - Send message (REST)
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

## Testing

```bash
# Run all tests
pytest backend/tests/ -v

# Run specific test file
pytest backend/tests/unit/test_tools.py -v

# With coverage
pytest backend/tests/ --cov=backend/app --cov-report=html
```

## Current Status

### ✅ Completed
- [x] Multi-agent LangGraph architecture
- [x] Router Agent with keyword + LLM dual strategy
- [x] 4 specialist agents with 13 tools
- [x] HITL approval queue
- [x] WebSocket real-time chat
- [x] MiniMax LLM integration
- [x] React frontend (Chat, Admin, Dashboard)
- [x] Unit tests (28 passing)
- [x] Project documentation (architecture, API, requirements)

### 🚧 In Progress
- [ ] Router Agent stability (MiniMax API inconsistency debugging)
- [ ] Database integration (PostgreSQL)
- [ ] Redis integration (session persistence)
- [ ] Chroma vector DB (knowledge base)

### 📋 Planned
- [ ] Authentication & Authorization (JWT)
- [ ] Streaming responses (SSE)
- [ ] Rate limiting
- [ ] PII detection & redaction
- [ ] Integration & E2E tests
- [ ] Docker application containers
- [ ] CI/CD pipeline

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11+, FastAPI, LangGraph, LangChain |
| **Frontend** | React 19, TypeScript, Vite 6, Tailwind CSS, Zustand |
| **LLM** | MiniMax (OpenAI-compatible API) |
| **Database** | PostgreSQL 15 (planned), Redis 7 (planned) |
| **Vector DB** | Chroma (planned) |
| **Testing** | pytest, 28 unit tests |
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
