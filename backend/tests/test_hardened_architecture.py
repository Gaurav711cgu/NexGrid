import pytest
import asyncio
from app.services.ast_chunker import ast_chunker
from app.services.sandbox_service import sandbox_engine
from app.services.crdt_service import crdt_service
from app.services.ai_service import ai_service
from app.core.telemetry import telemetry_manager


@pytest.mark.asyncio
async def test_ast_code_chunker_extraction():
    """Verify AST parsing extracts functions, classes, and imports correctly."""
    sample_code = """import os
import math

def calculate_area(radius):
    return math.pi * (radius ** 2)

class Circle:
    def __init__(self, r):
        self.r = r
"""
    chunks = ast_chunker.chunk_python_code(sample_code)
    assert len(chunks) >= 3
    chunk_types = [c.chunk_type for c in chunks]
    assert "imports" in chunk_types
    assert "function" in chunk_types
    assert "class" in chunk_types


@pytest.mark.asyncio
async def test_sandbox_execution_and_fallback():
    """Verify code execution in sandbox engine and security policy enforcement."""
    # 1. Normal safe Python execution
    res = await sandbox_engine.execute("print('FAANG Sandbox Verified')", language="python")
    assert res.exit_code == 0
    assert "FAANG Sandbox Verified" in res.stdout
    assert res.blocked is False
    assert "sandbox_driver" in res.metadata

    # 2. Blocked dangerous execution
    blocked_res = await sandbox_engine.execute("import os\nos.system('echo hacked')", language="python")
    assert blocked_res.blocked is True
    assert blocked_res.exit_code == -1
    assert "Security Policy Violation" in blocked_res.stderr


@pytest.mark.asyncio
async def test_crdt_redis_streams_delta_replay():
    """Verify CRDT stream delta processing and sequence replay."""
    room_id = "test_stream_room_99"
    update_data = b"\x01\x02\x03\x04FAANG_DELTA_TEST"

    seq_id = await crdt_service.process_update(room_id, update_data, sender_id="user_test_1")
    assert seq_id is not None

    missing = await crdt_service.get_missing_updates(room_id, last_seq_id="-")
    assert len(missing) >= 1
    assert update_data in missing or any(update_data in item for item in missing)


@pytest.mark.asyncio
async def test_ai_multi_provider_router_failover():
    """Verify AI service failover to fallback generator when APIs are unconfigured."""
    tokens = []
    async for token in ai_service.stream_completion(
        action="explain",
        code="def hello(): pass",
        language="python",
        room_id="test_room_ai"
    ):
        tokens.append(token)

    full_text = "".join(tokens)
    assert len(full_text) > 0
    assert "Code Overview" in full_text or "Python" in full_text or "def hello" in full_text


@pytest.mark.asyncio
async def test_opentelemetry_tracer_initialization():
    """Verify OpenTelemetry tracer initialization and span creation."""
    with telemetry_manager.create_span("test_span"):
        pass
    assert telemetry_manager is not None
