import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.services.sandbox_service import sandbox_engine
from app.auth.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token, blacklist_jti

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_security_hashing():
    pw = "SecretPassword123!"
    hashed = hash_password(pw)
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_dual_token_generation_and_decode():
    user_data = {"id": "test-id", "email": "test@example.com", "display_name": "Test User"}
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token(user_data)

    access_payload = asyncio.run(decode_token(access_token, expected_type="access"))
    assert access_payload["email"] == "test@example.com"
    assert "jti" in access_payload

    refresh_payload = asyncio.run(decode_token(refresh_token, expected_type="refresh"))
    assert refresh_payload["email"] == "test@example.com"
    assert "jti" in refresh_payload

def test_redis_token_blacklisting():
    user_data = {"id": "test-id-2", "email": "revoke@example.com", "display_name": "Revoke User"}
    token = create_access_token(user_data)
    payload = asyncio.run(decode_token(token, expected_type="access"))
    
    jti = payload["jti"]
    asyncio.run(blacklist_jti(jti))

    with pytest.raises(Exception) as exc_info:
        asyncio.run(decode_token(token, expected_type="access"))
    assert "revoked" in str(exc_info.value).lower() or "blacklisted" in str(exc_info.value).lower()

def test_sandbox_python_execution():
    code = "print('NexaGrid Sandbox Test')"
    res = asyncio.run(sandbox_engine.execute(code, "python"))
    assert res.exit_code == 0
    assert "NexaGrid Sandbox Test" in res.stdout
    assert res.blocked is False

def test_sandbox_blocked_dangerous_code():
    code = "import os\nos.system('echo Hacked')"
    res = asyncio.run(sandbox_engine.execute(code, "python"))
    assert res.blocked is True
    assert "Security Policy Violation" in res.stderr
