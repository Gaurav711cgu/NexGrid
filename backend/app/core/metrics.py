from prometheus_client import Gauge, Counter, Histogram

# ─── WebSocket Connections ────────────────────────────────────────────────────

# FIX-6: Removed room_id label — unbounded UUID cardinality crashes Prometheus memory.
# Use aggregate count across all rooms instead.
WS_CONNECTIONS_ACTIVE = Gauge(
    "ws_connections_active_total",
    "Total active WebSocket connections across all rooms",
)

# Per-room gauge only when you need to debug a specific room (not stored in Prometheus)
# Use: WS_CONNECTIONS_ACTIVE.set(total_across_all_rooms)

# ─── CRDT Operations ─────────────────────────────────────────────────────────

# FIX-6: Removed room_id label — was a cardinality bomb (1 time-series per room UUID).
CRDT_OPS_TOTAL = Counter(
    "crdt_ops_total",
    "Total CRDT Y.js operations processed across all rooms",
)

# ─── Code Execution ───────────────────────────────────────────────────────────

EXECUTION_DURATION = Histogram(
    "code_execution_seconds",
    "Code execution duration in seconds",
    ["language"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

EXECUTION_BLOCKED = Counter(
    "code_executions_blocked_total",
    "Total code executions blocked by static analysis or resource limits",
    ["reason", "language"],
)

# Queue depth: how many executions are pending right now
EXECUTION_QUEUE_DEPTH = Gauge(
    "code_execution_queue_depth",
    "Number of code execution requests currently queued or in-flight",
)

# ─── AI Completion ────────────────────────────────────────────────────────────

AI_COMPLETION_DURATION = Histogram(
    "ai_completion_seconds",
    "Time to first token from AI model",
    ["model", "action"],
    buckets=(0.1, 0.3, 0.5, 0.8, 1.2, 2.0, 5.0),
)

AI_TOKEN_USAGE = Counter(
    "ai_tokens_total",
    "Total AI tokens used (input + output)",
    ["model", "direction"],  # direction: input | output
)

# ─── AI Semantic Cache ────────────────────────────────────────────────────────
AI_CACHE_HITS = Counter(
    "ai_cache_hits_total",
    "Total AI completions served directly from Semantic Cache without API call",
)

AI_CACHE_MISSES = Counter(
    "ai_cache_misses_total",
    "Total AI completions resulting in cache miss and routed to LLM provider",
)

# ─── Circuit Breaker ──────────────────────────────────────────────────────────

# FIX-6 addition: circuit breaker state for Grafana alert rule
# Values: 0=CLOSED (healthy), 1=OPEN (failing), 2=HALF_OPEN (probing)
CIRCUIT_BREAKER_STATE = Gauge(
    "circuit_breaker_state",
    "Current state of the AI service circuit breaker (0=CLOSED, 1=OPEN, 2=HALF_OPEN)",
    ["service"],  # e.g., "anthropic_claude"
)

# ─── Room Activity ────────────────────────────────────────────────────────────

# FIX-6: Keep room_id label only on short-lived operational gauges that are reset
# when a room closes — not on ever-growing counters.
ROOM_PARTICIPANT_COUNT = Gauge(
    "room_participant_count",
    "Current active participants in a room",
    ["room_id"],  # Acceptable here: rooms are finite and gauges are cleaned up on close
)
