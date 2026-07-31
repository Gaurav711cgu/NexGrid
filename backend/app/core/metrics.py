from prometheus_client import Gauge, Counter, Histogram

# Active WebSocket connections gauge
WS_CONNECTIONS_ACTIVE = Gauge(
    "ws_connections_active",
    "Active WebSocket connections count",
    ["room_id"]
)

# Total CRDT operations processed
CRDT_OPS_TOTAL = Counter(
    "crdt_ops_total",
    "Total CRDT operations processed",
    ["room_id"]
)

# Code execution latency histogram
EXECUTION_DURATION = Histogram(
    "code_execution_seconds",
    "Code execution duration in seconds",
    ["language"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Blocked executions counter (security static analysis triggers)
EXECUTION_BLOCKED = Counter(
    "code_executions_blocked_total",
    "Total code executions blocked by static analysis or limits",
    ["reason", "language"]
)

# AI completion duration histogram
AI_COMPLETION_DURATION = Histogram(
    "ai_completion_seconds",
    "Time to complete AI generation in seconds",
    ["model", "action"],
    buckets=(0.1, 0.3, 0.5, 0.8, 1.2, 2.0, 5.0)
)

# Room participant peak gauge
ROOM_PARTICIPANT_COUNT = Gauge(
    "room_participant_count",
    "Current active participants in a room",
    ["room_id"]
)
