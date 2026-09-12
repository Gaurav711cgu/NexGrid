import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.sandbox_service import sandbox_engine
from app.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    blacklist_jti,
)

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_security_hashing():
    pw = "SecretPassword123!"
    hashed = hash_password(pw)
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


@pytest.mark.asyncio
async def test_dual_token_generation_and_decode():
    user_data = {"id": "test-id", "email": "test@example.com", "display_name": "Test User"}
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token(user_data)

    access_payload = await decode_token(access_token, expected_type="access")
    assert access_payload["email"] == "test@example.com"
    assert "jti" in access_payload

    refresh_payload = await decode_token(refresh_token, expected_type="refresh")
    assert refresh_payload["email"] == "test@example.com"
    assert "jti" in refresh_payload


@pytest.mark.asyncio
async def test_redis_token_blacklisting():
    user_data = {"id": "test-id-2", "email": "revoke@example.com", "display_name": "Revoke User"}
    token = create_access_token(user_data)
    payload = await decode_token(token, expected_type="access")

    jti = payload["jti"]
    await blacklist_jti(jti)

    with pytest.raises(Exception) as exc_info:
        await decode_token(token, expected_type="access")
    assert "revoked" in str(exc_info.value).lower() or "blacklisted" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_sandbox_python_execution():
    code = "print('NexaGrid Sandbox Test')"
    res = await sandbox_engine.execute(code, "python")
    assert res.exit_code == 0
    assert "NexaGrid Sandbox Test" in res.stdout
    assert res.blocked is False


@pytest.mark.asyncio
async def test_sandbox_blocked_dangerous_code():
    code = "import os\nos.system('echo Hacked')"
    res = await sandbox_engine.execute(code, "python")
    assert res.blocked is True
    assert "Security Policy Violation" in res.stderr


def test_mcp_tool_list(client):
    response = client.post("/api/mcp/tools/list")
    assert response.status_code == 200
    tools = response.json()["tools"]
    tool_names = [t["name"] for t in tools]
    assert "nexgrid_create_room" in tool_names
    assert "nexgrid_execute_sandbox" in tool_names
    assert "nexgrid_get_analytics" in tool_names


def test_mcp_execute_sandbox_tool(client):
    user_data = {"id": "test-mcp-user", "email": "mcpuser@example.com", "display_name": "MCP User"}
    token = create_access_token(user_data)
    req = {
        "name": "nexgrid_execute_sandbox",
        "arguments": {"code": "print('MCP Execution Success')", "language": "python"},
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/mcp/tools/execute", json=req, headers=headers)
    assert response.status_code == 200
    content = response.json()["content"][0]["text"]
    assert "MCP Execution Success" in content


@pytest.mark.asyncio
async def test_sandbox_rust_security_check():
    code = "use std::process::Command;\nfn main() { Command::new('ls').output(); }"
    res = await sandbox_engine.execute(code, "rust")
    assert res.blocked is True
    assert "Security Policy Violation" in res.stderr


@pytest.mark.asyncio
async def test_sandbox_java_security_check():
    code = 'public class Main { public static void main(String[] args) { Runtime.getRuntime().exec("ls"); } }'
    res = await sandbox_engine.execute(code, "java")
    assert res.blocked is True
    assert "Security Policy Violation" in res.stderr
