import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth.security import create_access_token
from app.services.rate_limiter import SlidingWindowRateLimiter
from app.services.circuit_breaker import CircuitBreaker, CircuitState

client = TestClient(app)


def get_auth_header():
    user = {"id": "usr-100", "email": "testrooms@nexagrid.dev", "display_name": "Room Tester"}
    token = create_access_token(user)
    return {"Authorization": f"Bearer {token}"}


def test_create_and_get_room():
    headers = get_auth_header()
    with TestClient(app) as test_client:
        # Create room
        create_res = test_client.post(
            "/api/rooms",
            json={"name": "Test Algo Room", "language": "python", "is_public": True},
            headers=headers,
        )
        assert create_res.status_code == 201
        room = create_res.json()
        assert room["name"] == "Test Algo Room"
        assert "code" in room
        room_code = room["code"]

        # Get room by code (with auth header)
        get_res = test_client.get(f"/api/rooms/{room_code}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["code"] == room_code


def test_execute_code_endpoint():
    headers = get_auth_header()
    res = client.post(
        "/api/execution/test-room-123/run",
        json={"code": "print('Hello from REST Execution API')", "language": "python"},
        headers=headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["exit_code"] == 0
    assert "Hello from REST Execution API" in body["stdout"]


@pytest.mark.asyncio
async def test_sliding_window_rate_limiter():
    limiter = SlidingWindowRateLimiter(requests_limit=3, window_seconds=60)
    user_id = "test-user-rate-limit"

    allowed1, remaining1 = await limiter.is_allowed(user_id)
    assert allowed1 is True

    allowed2, remaining2 = await limiter.is_allowed(user_id)
    assert allowed2 is True

    allowed3, remaining3 = await limiter.is_allowed(user_id)
    assert allowed3 is True

    allowed4, remaining4 = await limiter.is_allowed(user_id)
    assert allowed4 is False
    assert remaining4 == 0


def test_circuit_breaker_state_machine():
    cb = CircuitBreaker(failure_threshold=2, recovery_time_seconds=1)
    assert cb.state == CircuitState.CLOSED
    assert cb.allow_request() is True

    # 1st failure
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED

    # 2nd failure -> Trips OPEN
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.allow_request() is False

    # Reset on success
    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb.allow_request() is True
