import pytest
from unittest.mock import patch, MagicMock
from app.services.ai_service import generate_code_completion
from app.services.circuit_breaker import ai_circuit_breaker

@pytest.fixture(autouse=True)
def reset_circuit_breaker():
    ai_circuit_breaker.reset()
    yield

def test_circuit_breaker_nominal_flow():
    assert ai_circuit_breaker.state == "CLOSED"
    ai_circuit_breaker.record_success()
    assert ai_circuit_breaker.state == "CLOSED"

def test_circuit_breaker_opens_after_failures():
    for _ in range(ai_circuit_breaker.failure_threshold):
        ai_circuit_breaker.record_failure()
    assert ai_circuit_breaker.state == "OPEN"

def test_circuit_breaker_half_open_transition():
    # Force open
    ai_circuit_breaker.state = "OPEN"
    ai_circuit_breaker.last_failure_time = 0 # Unix epoch
    
    # Should transition to half open on next check since cooldown passed
    assert ai_circuit_breaker.allow_request() is True
    assert ai_circuit_breaker.state == "HALF_OPEN"

def test_circuit_breaker_half_open_success():
    ai_circuit_breaker.state = "HALF_OPEN"
    ai_circuit_breaker.record_success()
    assert ai_circuit_breaker.state == "CLOSED"

def test_circuit_breaker_half_open_failure():
    ai_circuit_breaker.state = "HALF_OPEN"
    ai_circuit_breaker.record_failure()
    assert ai_circuit_breaker.state == "OPEN"
