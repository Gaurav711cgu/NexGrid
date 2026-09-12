# NexGrid

NexGrid is a Tier-1, globally distributed real-time code execution platform. Built with Y.js CRDTs, a Redis Streams backplane, and a hybrid POSIX/Docker execution engine, it provides ultra-low latency pair programming with a hardened, AI-assisted architecture.

## Key Features

- **Global Edge Routing**: Terminated WebSockets at the edge with room affinity, reducing cross-region latency to under 50ms.
- **Y.js CRDT Engine**: Decentralized, conflict-free state synchronization backed by Redis Streams.
- **Semantic AI Router**: Intelligent LLM routing (Anthropic/Local) augmented by Vector RAG, AST chunking, and Semantic Caching.
- **Hardened Sandboxing**: Multi-tenant execution environment secured by gVisor Docker containers and strict CPU/memory token-bucket limiters.
- **Production-Grade MLOps**: Automated evaluation pipelines tracking groundedness, latency, and cache hit rates.

---

## Tech Stack

- **Frontend**: React 18, Vite, Tailwind CSS, Framer Motion, Monaco Editor (`y-monaco`)
- **Backend**: Python 3.11, FastAPI, SQLAlchemy (Async), Alembic
- **Real-Time Data**: Y.js (CRDT), WebSockets, Upstash Redis Streams
- **Database**: PostgreSQL 16 (via asyncpg)
- **AI/MLOps**: LangChain, Vector RAG, Lexical/Groundedness Evaluators
- **Infrastructure**: Terraform, Docker, Fly.io, GitHub Actions
- **Observability**: Prometheus, OpenTelemetry, Grafana

---

## Prerequisites

- Node.js 20+
- Python 3.11+
- PostgreSQL 16+ (or Docker)
- Redis 7+ (or Upstash account)
- Docker (for local execution sandbox)

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Gaurav711cgu/NexGrid.git
cd NexGrid
```

### 2. Backend Setup (FastAPI)

Ensure Python 3.11+ is installed, then set up your virtual environment:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements.dev.txt
```

### 3. Frontend Setup (React/Vite)

```bash
cd ../frontend
npm install
```

### 4. Environment Variables

Copy the example environment files in the backend:

```bash
cd ../backend
cp .env.example .env
```

Configure your `.env` variables:

| Variable | Description | Example |
| -------- | ----------- | ------- |
| `DATABASE_URL` | PostgreSQL Async connection string | `postgresql+asyncpg://user:pass@localhost:5432/nexagrid` |
| `REDIS_URL` | Redis Streams Backplane | `redis://localhost:6379/0` |
| `JWT_SECRET` | Token signing secret | `your-secure-secret` |
| `ANTHROPIC_API_KEY` | Anthropic Claude API Key | `sk-ant-api03-...` |
| `ENVIRONMENT` | Deployment environment | `development` |

### 5. Database Setup

Ensure PostgreSQL is running. Then, run the Alembic migrations to set up your schema:

```bash
# In the backend directory:
alembic upgrade head
```

### 6. Start the Development Servers

We recommend running the backend and frontend in separate terminals.

**Terminal 1 (Backend + WebSockets):**
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Architecture

### Directory Structure

```text
├── backend/
│   ├── alembic/              # Database migrations
│   ├── app/
│   │   ├── api/              # FastAPI Routers
│   │   ├── core/             # Config, DB, Redis, Telemetry
│   │   ├── models/           # SQLAlchemy schemas & Pydantic models
│   │   ├── prompts/          # AI Prompt Registry
│   │   ├── services/         # Business logic (Circuit Breakers, Evals, Cache, RAG)
│   │   └── websocket/        # Real-time Y.js CRDT & Presence Sync
│   ├── tests/                # Pytest async test suite
│   ├── Dockerfile
│   └── alembic.ini
├── frontend/
│   ├── src/
│   │   ├── components/       # UI (Editor, Room, Auth, Navigation)
│   │   ├── hooks/            # Custom React hooks (useYjsDoc, useAIStream)
│   │   ├── lib/              # API and utility functions
│   │   └── styles/           # Tailwind and token definitions
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
├── infra/                    # Terraform configurations
├── mlops/                    # Airflow/Prefect DAGs for continuous evaluation
├── benchmarks/               # Locust Load Testing reports
└── docs/                     # Architectural Decision Records (ADRs)
```

### Request & Data Lifecycle

1. **Client Connection:** User joins a Room via the frontend; a WebSocket connection is established to the closest edge node.
2. **State Sync:** `y-websocket` negotiates state vectors. The backend persists binary CRDT updates into **Redis Streams**.
3. **Execution:** Code submitted for execution is routed to a token-bucket rate limiter, then dispatched to a temporary `gVisor` Docker sandbox or WASM engine.
4. **AI Assistant:** Chat queries are intercepted by the **Semantic Cache**. On a miss, the AST Chunker isolates relevant code blocks, builds a Vector RAG context, and routes to Anthropic (falling back to local LLMs via Circuit Breaker on failure).

### Key Subsystems

- **Circuit Breaker (`backend/app/services/circuit_breaker.py`)**: Protects against downstream LLM outages. Transitions strictly through `CLOSED` -> `OPEN` -> `HALF_OPEN`.
- **Semantic Cache (`backend/app/services/semantic_cache.py`)**: Saves API costs by matching incoming queries against a vector index of previously resolved AST-bound questions.
- **MLOps Pipeline (`mlops/pipelines/daily_eval_pipeline.py`)**: Periodically re-indexes the vector database and runs Lexical/Groundedness regression checks on the AI's responses using a Golden Dataset.

---

## Available Scripts

### Backend

| Command | Description |
| ------- | ----------- |
| `uvicorn app.main:app --reload` | Start FastAPI development server |
| `alembic upgrade head` | Run all pending migrations |
| `alembic revision --autogenerate` | Create a new migration script |
| `pytest backend/tests` | Run the backend test suite |
| `locust -f backend/tests/load/locustfile.py` | Run 500 VU load test simulation |

### Frontend

| Command | Description |
| ------- | ----------- |
| `npm run dev` | Start Vite dev server |
| `npm run build` | Compile optimized production build |
| `npm run preview` | Preview production build locally |

---

## Testing

NexGrid uses `pytest` with `pytest-asyncio` for robust backend testing.

```bash
# Run all tests
pytest backend/tests

# Run tests with verbose output
pytest backend/tests -v

# Test only the AI evaluation pipeline
pytest backend/tests/test_ai_evals.py
```

*Frontend testing (Vitest/Playwright) pipeline is configured in the CI/CD pipeline.*

---

## Deployment

NexGrid is designed to be deployed using Docker on edge platforms like Fly.io or Render.

### Docker Compose (Local/Staging)

```bash
docker-compose -f docker-compose.staging.yml up --build -d
```
This spins up Postgres, Redis, Prometheus, Grafana, and the NexGrid application containers.

### Fly.io (Production)

Configuration lives in `backend/fly.toml`.

```bash
cd backend
fly launch
fly secrets set DATABASE_URL="..." REDIS_URL="..." ANTHROPIC_API_KEY="..."
fly deploy
```

### Terraform Infrastructure

```bash
cd infra
terraform init
terraform apply
```

---

## Troubleshooting

### WebSocket Disconnections / Sync Errors
**Error:** Cursors not appearing or code de-syncing.
**Solution:** Ensure your local Redis instance is running and accessible. The Y.js backplane requires Redis Pub/Sub to broadcast updates across workers. Check connection limits in `app/core/database.py` (Default asyncpg pool size is tuned to 100).

### Alembic Migration Errors
**Error:** `Target database is not up to date.`
**Solution:**
```bash
alembic current
alembic stamp head
alembic upgrade head
```

### Sandbox Resource Limits
**Error:** Code execution fails with `Memory Limit Exceeded`.
**Solution:** The POSIX/Docker sandbox strictly limits memory (e.g., 50MB per process). If testing locally with heavy ML scripts, increase the bounds in `backend/app/services/sandbox_service.py` under the `_run_docker_isolated` configuration.
