import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth.security import create_access_token, blacklist_jti, decode_token

def test_auth_unauthenticated_request_rejected(client):
    """Unauthenticated requests to protected endpoints return 401."""
    response = client.post(
        "/api/execution/test-room-id/run",
        json={"code": "print(1)", "language": "python"},
    )
    assert response.status_code == 401
    assert "Authentication required" in response.json()["detail"]


def test_auth_register_and_login_flow(client):
    """User registration and login return access token and set HttpOnly refresh cookie."""
    test_email = "tester_unique@nexagrid.dev"
    test_password = "SecurePassword123!"

    # 1. Register
    reg_response = client.post(
        "/api/auth/register",
        json={
            "email": test_email,
            "password": test_password,
            "display_name": "Test Runner",
        },
    )
    # 201 created or 400 if already existing from prior run
    assert reg_response.status_code in [201, 400]

    # 2. Login
    login_response = client.post(
        "/api/auth/login",
        json={"email": test_email, "password": test_password},
    )
    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == test_email
    assert "nexagrid_refresh_token" in login_response.cookies


@pytest.mark.asyncio
async def test_auth_token_revocation():
    """Revoked JTI tokens cannot be decoded."""
    user_data = {"id": "rev-id-1", "email": "rev@nexagrid.dev", "display_name": "Rev"}
    token = create_access_token(user_data)
    payload = await decode_token(token, expected_type="access")

    jti = payload["jti"]
    await blacklist_jti(jti)

    with pytest.raises(Exception):
        await decode_token(token, expected_type="access")


def test_auth_ws_ticket_issuance(client):
    """Authenticated users can acquire a 60-second single-use WebSocket connection ticket."""
    user_data = {"id": "ws-user-1", "email": "ws@nexagrid.dev", "display_name": "WS User"}
    token = create_access_token(user_data)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/auth/ws-ticket", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "ticket" in data
    assert data["expires_in"] == 60

