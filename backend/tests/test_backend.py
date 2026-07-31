import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.services.sandbox_service import sandbox_engine
from app.auth.security import hash_password, verify_password, create_access_token

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
