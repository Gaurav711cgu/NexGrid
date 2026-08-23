# NexGrid — Production Requirements Document

**Domain:** Distributed Systems / Real-Time Collaboration  
**Status:** 🟢 NEAR-PRODUCTION — one sprint from FAANG-defensible  
**Target Roles:** FAANG SDE, Systems Infra, Backend L4/L5  
**Stack:** FastAPI · PostgreSQL · Redis · Y.js CRDT · WebSocket · Docker · Prometheus/Grafana

---

## 1. Problem Statement

### What It Solves

Real-time collaborative code editing with isolated, multi-language sandboxed execution. Specifically: how do you let N users edit shared code simultaneously without merge conflicts, while executing that code safely without host OS compromise?

### Why It's Hard (Engineering Significance)

Off-the-shelf solutions (ShareDB, Firepad) use Operational Transformation (OT), which has O(N²) message complexity and requires a centralized transform server. Y.js CRDT is mathematically convergent without coordination — any two users can independently apply edits and produce identical documents without a central arbiter. This is the same approach used by Linear, Notion, and Figma.

Sandboxed execution requires OS-level isolation: a Node.js `vm` module or Python `exec()` call can escape into the host process's memory space. POSIX `setrlimit` applies kernel-enforced resource caps per-process that cannot be bypassed from user space.

### Quantified Stakes

- Collaborative editors at FAANG (Colab, Cloud Shell, Replit) serve thousands of concurrent sessions — each session is a CRDT actor
- Sandbox escapes in coding platforms are CVEs (Replit had one in 2023) — POSIX sandboxing is the production mitigation

---

## 2. System Architecture

```
                        ┌─────────────────────┐
Client A ──WebSocket──→ │                     │
Client B ──WebSocket──→ │  FastAPI WS Server  │──→ Redis Pub/Sub ──→ Fan-out to all room clients
Client C ──WebSocket──→ │                     │
                        └──────────┬──────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
        Y.js CRDT Engine    PostgreSQL (WAL)      POSIX Sandbox
        (Document State)    (Persistence Layer)   Executor
              │                    │               Python/JS/Go/Rust/Java
        Redis Pub/Sub         Cursor O(1)          setrlimit:
        (Broadcast)           Pagination           RLIMIT_AS=128MB
                                                   RLIMIT_CPU=5s
                                                   RLIMIT_NPROC=10
              ▼
        Prometheus /metrics → Grafana Dashboard
```

### Component Breakdown

| Component | Responsibility | Key Implementation |
|---|---|---|
| CRDT Engine | Conflict-free document merging | Y.js; ops are commutative, associative, idempotent |
| WebSocket Fan-out | Broadcast edits to all room participants | Redis Pub/Sub (not polling) |
| Sandbox Executor | Safe multi-language code execution | POSIX `setrlimit` — kernel-enforced, cannot be bypassed |
| Auth Layer | Token lifecycle management | Dual-token JWT with JTI blacklist in Redis (O(1) revocation) |
| Pagination | Efficient room/history listing | Cursor-based O(1) vs OFFSET O(N) — explicit trade-off |
| Circuit Breaker | LLM completion resilience | CLOSED → OPEN → HALF_OPEN state machine |
| Telemetry | Observability | Prometheus scrape endpoint → Grafana dashboards |
| MCP Server | AI agent tool registry | `/api/mcp/tools/list` exposes `nexgrid_create_room`, `nexgrid_execute_sandbox` |
| Session Replay | CRDT trajectory recording | `room_events` table; `GET /rooms/{id}/replay` replays ordered op sequence |
| AI Debug Mode | Automated error diagnosis | `POST /execution/{room_id}/debug` streams Claude fix suggestions on failure |

---

## 3. Architecture Decision Records (ADRs)

> Full ADRs are in [`docs/decisions/`](./decisions/)

| Decision | Alternatives Considered | Chosen | Rationale |
|---|---|---|---|
| CRDT algorithm | Operational Transformation (OT), WOOT, Logoot | **Y.js (YATA variant)** | OT requires centralized server; Y.js is server-agnostic and handles partition tolerance. Industry standard (Notion, Linear) |
| Token revocation | Short-lived access tokens only, Opaque tokens + DB lookup | **JWT + JTI Redis blacklist** | Short-lived tokens don't support instant revocation on logout/compromise; DB lookup is O(log N); Redis JTI is O(1) |
| Sandbox isolation | Docker container per execution, `subprocess` with timeout, seccomp-bpf | **POSIX `setrlimit`** | Docker per-run has >500ms cold start; `subprocess` doesn't prevent fork bombs; `setrlimit` is kernel-enforced with ~2ms overhead |
| Pagination | OFFSET-based, keyset/cursor | **Cursor-based (O(1))** | OFFSET requires table scan to row N; cursor uses index seek — documented with query plans |
| WebSocket broadcast | Direct WS send per connection, Server-Sent Events | **Redis Pub/Sub fan-out** | Enables horizontal scaling across multiple FastAPI workers without shared memory |
| LLM integration | Direct synchronous call, Queue-based async | **Circuit breaker + streaming** | LLM latency is unpredictable (p99 > 10s); circuit breaker prevents cascade failure when LLM is degraded |
| Password hashing | `hashlib.pbkdf2_hmac`, MD5, SHA-256 | **bcrypt via passlib** | bcrypt has adaptive cost factor (work factor); PBKDF2 with static salt is vulnerable to rainbow tables |
| Rate limiting | Fixed window counter, Token bucket | **Redis Sorted Set sliding window** | Fixed window allows 2× burst at boundary; sliding window enforces strict per-second caps |

---

## 4. Performance Profile

### Measured Benchmarks

> Benchmarks run on local dev (MacBook Pro M2). Load tests committed to `benchmarks/results/`.

| Metric | Value | Measurement Method |
|---|---|---|
| CRDT broadcast p50 | **8.1ms** | Locust WebSocket test, 50 concurrent users |
| CRDT broadcast p95 | **14.2ms** | Locust WebSocket test, 50 concurrent users |
| Room preload latency p50 | **18.4ms** | Cursor pagination query, 10k rows |
| Python execution p50 | **120.2ms** | Subprocess + POSIX limits |
| AI first-token latency p50 | **210ms** | Claude Haiku streaming |
| Token revocation lookup | **O(1)** | Redis SISMEMBER — hash-indexed |
| History query (deep page 100) | **5.2ms p50** | Composite index cursor vs OFFSET |
| Concurrent users tested | **50** | Locust load test — steady-state, no errors |

### How to Reproduce

```bash
# Prerequisites: Docker Compose up, Python 3.11+
cd backend/tests/load/
pip install locust
locust -f locustfile.py --host=http://localhost:8000 \
  --users 50 --spawn-rate 5 --run-time 60s --headless

# HTML report saved to benchmarks/results/locust_report.html
```

> ⚠️ **Gap (P2):** Load test currently uses 50 VU. Needs 200-VU run with documented p95/p99 and results committed to `benchmarks/results/` before FAANG interview.

---

## 5. Security Model

### Defense-in-Depth Layers (Sandbox)

| Layer | Mechanism | Bypass Risk |
|---|---|---|
| Static AST analysis | Python `ast.walk` blocks `os`, `subprocess`, `ctypes` imports | Low — pre-execution |
| Process isolation | `asyncio.create_subprocess_exec` — child process | Medium — escapes contained |
| Memory cap | `RLIMIT_AS = 128MB` | None — kernel-enforced OOM |
| CPU cap | `RLIMIT_CPU = 5s` | None — kernel SIGKILL |
| Fork bomb prevention | `RLIMIT_NPROC = 10` | None — kernel-enforced |
| Timeout | `asyncio.wait_for(timeout=10s)` | None — async cancellation |
| Temp dir isolation | `tempfile.TemporaryDirectory()` — auto-cleaned | Low — ephemeral |

> **Production upgrade path:** Replace POSIX `setrlimit` with **gVisor** (Google's OCI runtime sandbox used in Cloud Run) or **Firecracker microVMs** (AWS Lambda's isolation primitive) for defence-in-depth at the hypervisor level.

### Authentication & Session Security

| Property | Implementation |
|---|---|
| Password hashing | `bcrypt` (work factor 12) — adaptive, rainbow-table-resistant |
| Access token lifetime | 15 minutes (short-lived) |
| Refresh token lifetime | 7 days — `HttpOnly; SameSite=Lax` cookie |
| Instant revocation | JTI UUID blacklisted in Redis on logout; O(1) lookup on every request |
| Token rotation | Every `/refresh` call blacklists old refresh JTI and issues new pair |
| CORS | Origin allowlist from `CORS_ALLOWED_ORIGINS` env var — no wildcard in production |

---

## 6. System Contract

### SLAs (Design Targets)

| Guarantee | Target | Enforcement |
|---|---|---|
| CRDT broadcast latency | p50 < 10ms | Redis Pub/Sub — no DB write on broadcast path |
| Code execution timeout | ≤ 5s CPU / ≤ 10s wall-clock | `RLIMIT_CPU` (kernel) + `asyncio.wait_for` |
| Sandbox memory cap | 128MB | `RLIMIT_AS` — OS OOM kills beyond this |
| Token revocation | Immediate (next request) | JTI checked on every authenticated endpoint |
| LLM completion resilience | Fails open (circuit breaker) | `OPEN` state returns 503 after 5 consecutive failures |
| Rate limiting | 60 requests / 60s per user | Redis sorted-set sliding window pipeline |

### Consistency Model

| Data | Model | Guarantee |
|---|---|---|
| Document state | **CvRDT (convergent)** | Eventual consistency — mathematical convergence |
| Session auth | **Strong consistency** | Synchronous Redis JTI lookup on every request |
| Execution results | **At-most-once** | Sandbox runs are not retried on timeout |
| Room events (replay) | **Sequential consistency** | Events ordered by `seq_num` — monotonically increasing |

### Known Failure Modes

| Failure | Behavior | Recovery |
|---|---|---|
| Redis down | WebSocket fan-out falls back to in-process dict; cross-node broadcast lost | Reconnect; document reloaded from PostgreSQL snapshot |
| LLM provider down | Circuit breaker `OPEN`; AI endpoints return 503 | Auto-reset after 60s (`HALF_OPEN` probe) |
| Sandbox OOM | Child process killed by OS; error message returned to client | No host impact; error surfaced via `stderr` |
| PostgreSQL exhausted | HTTP 500 on new sessions | Connection pool `min_size=5, max_size=20` with `command_timeout=30` |
| Rate limiter Redis error | Fail-open (allow request) + log error | Redis reconnect; brief window of unmetered execution |

---

## 7. Test Coverage & Correctness

| Category | Status | Notes |
|---|---|---|
| Unit — sandbox security | ✅ | Python AST, Rust/Java pattern checks |
| Unit — auth (bcrypt, JWT, JTI) | ✅ | Token generation, blacklisting, decode |
| Integration — MCP tool server | ✅ | List + execute tool round-trip |
| Integration — session replay | ✅ | Event recording + replay ordering |
| WebSocket — CRDT lifecycle | 🔶 P1 | Needs `pytest-anyio` WS client tests |
| Auth flow — cookie rotation | 🔶 P1 | `/refresh` and `/logout` endpoint tests |
| Load test — 200 VU | 🔶 P2 | Currently at 50 VU |
| Coverage threshold | 85% target (70% current) | CI `--cov-fail-under=85` after P1 |
| Security scan | ✅ Bandit clean | `bandit -r backend/app -ll` |
| Dependency CVE scan | 🔶 P1 | `pip-audit` not yet in CI |

---

## 8. Known Limitations & Production Delta

| Limitation | Why It's Out of Scope | Production Solution |
|---|---|---|
| No staging environment | Solo project; cloud cost | `docker-compose.staging.yml` with env overrides |
| Load test at 50 VU, not 500+ | Local dev budget | Scale to 200+ VU; commit results before interviews |
| No Alembic migrations | Schema is stable during development | `alembic init` + expand/migrate/contract pattern |
| Single-region deployment | Demo project | Multi-region requires distributed Y.js + CRDT merge across regions |
| POSIX sandbox (Linux only) | OS dependency | gVisor (Cloud Run) or Firecracker (Lambda) for production |
| No per-WebSocket rate limiting | Demo scope | Token bucket per WS connection |
| No distributed tracing | Demo scope | OpenTelemetry → Jaeger/Tempo for span-level visibility |
| Static prompt strings | Demo scope | Versioned prompt registry with A/B eval harness |

### What Would Be Needed for Google-Scale

1. **Y.js persistence server** (y-websocket + LevelDB or y-mongodb) replacing custom Redis Pub/Sub
2. **Horizontal FastAPI workers** behind load balancer with WS sticky sessions
3. **gVisor** replaces POSIX setrlimit for hypervisor-level sandbox isolation
4. **Distributed tracing** (Jaeger/Tempo) with trace IDs propagated through every service
5. **Prompt versioning + eval harness** for AI pair programmer quality control
6. **Alembic migrations** with expand/contract pattern for zero-downtime schema changes

---

## 9. Interview Defense Points

**Q: Why CRDT over OT?**  
A: OT requires a central server to serialize concurrent operations; it breaks under network partition. CRDT ops are commutative and associative — order of arrival doesn't affect final state. For a distributed system that must handle partition, this is the mathematically correct choice.

**Q: Why Redis JTI instead of short-lived tokens only?**  
A: Short-lived tokens (5min) can't be invalidated immediately on logout or account compromise. The JTI blacklist is O(1) Redis lookup with TTL equal to token expiry — no DB fan-out, no polling.

**Q: How does the sandbox prevent fork bombs?**  
A: `RLIMIT_NPROC=10` caps the number of child processes a spawned subprocess can create. Combined with `RLIMIT_CPU=5s`, a fork bomb gets 10 processes for 5 seconds maximum before the OS kills all of them. The parent FastAPI process is completely unaffected.

**Q: Why cursor pagination instead of OFFSET?**  
A: OFFSET scans and discards N rows before returning results — O(N) at deep pages. Cursor uses a composite index seek `(executed_at DESC, id DESC)` — O(1) regardless of page depth. Critical at 10M+ execution log rows.

**Q: How does the circuit breaker protect the system?**  
A: After 5 consecutive LLM failures, the circuit opens and returns 503 immediately without hitting the API — preventing thread starvation on a degraded provider. After 60s, it enters HALF_OPEN and probes with one request. If that succeeds, it closes; if not, it opens again.

**Q: Why bcrypt over PBKDF2?**  
A: PBKDF2 with a static application-level salt means two users with the same password produce identical hashes — vulnerable to rainbow tables. bcrypt generates a random 128-bit salt per hash automatically, making per-hash attacks infeasible.

---

*Last updated: August 2026 | Maintainer: Gaurav Kumar Nayak | Target: FAANG SDE / Systems Infra / Backend L4/L5*
