import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Response, Request
from app.models.schemas import RegisterRequest, LoginRequest, AuthResponse
from app.auth.security import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    decode_token, blacklist_jti, get_current_user
)
from app.core.database import db
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])

COOKIE_NAME = "nexagrid_refresh_token"

def set_refresh_cookie(response: Response, refresh_token: str):
    """Set secure HttpOnly cookie for refresh token.
    FIX-3: secure flag is conditionally True in production — no more hardcoded False.
    """
    response.set_cookie(
        key=COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,  # 7 days
        samesite="lax",
        secure=settings.ENVIRONMENT == "production",
    )

@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(req: RegisterRequest, response: Response):
    existing = await db.fetchrow("SELECT id FROM users WHERE email = $1", req.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    pw_hash = hash_password(req.password)
    
    await db.execute(
        """INSERT INTO users (id, email, password_hash, display_name)
           VALUES ($1, $2, $3, $4)""",
        user_id, req.email, pw_hash, req.display_name
    )

    user_data = {"id": user_id, "email": req.email, "display_name": req.display_name}
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token(user_data)

    set_refresh_cookie(response, refresh_token)
    return AuthResponse(access_token=access_token, user=user_data)

@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, response: Response):
    user = await db.fetchrow("SELECT * FROM users WHERE email = $1", req.email)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_data = {"id": str(user["id"]), "email": user["email"], "display_name": user["display_name"]}
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token(user_data)

    set_refresh_cookie(response, refresh_token)
    return AuthResponse(access_token=access_token, user=user_data)

@router.post("/refresh")
async def refresh_tokens(request: Request, response: Response):
    """
    Enterprise Refresh Token Rotation:
    Validates HttpOnly refresh cookie, revokes old JTI in Redis, and issues new token pair.
    """
    refresh_token = request.cookies.get(COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token cookie missing")

    payload = await decode_token(refresh_token, expected_type="refresh")

    # Blacklist used refresh token JTI (Token Rotation Pattern)
    old_jti = payload.get("jti")
    if old_jti:
        await blacklist_jti(old_jti, ttl_seconds=60 * 60 * 24 * 7)

    user_data = {"id": payload["id"], "email": payload["email"], "display_name": payload["display_name"]}
    new_access_token = create_access_token(user_data)
    new_refresh_token = create_refresh_token(user_data)

    set_refresh_cookie(response, new_refresh_token)
    return {"access_token": new_access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(request: Request, response: Response, user: dict = Depends(get_current_user)):
    """
    Zero-Trust Session Revocation:
    Blacklists both access token JTI and refresh token JTI in Redis.
    """
    refresh_token = request.cookies.get(COOKIE_NAME)
    if refresh_token:
        try:
            refresh_payload = await decode_token(refresh_token, expected_type="refresh")
            jti = refresh_payload.get("jti")
            if jti:
                await blacklist_jti(jti, ttl_seconds=60 * 60 * 24 * 7)
        except Exception:
            pass  # token invalid/expired — still proceed with logout

    if "jti" in user:
        await blacklist_jti(user["jti"])

    response.delete_cookie(key=COOKIE_NAME)
    return {"message": "Logged out successfully. Tokens revoked."}

@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {"user": user}
