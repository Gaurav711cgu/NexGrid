import uuid
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from app.core.config import settings
from app.core.redis import redis_client

security_bearer = HTTPBearer(auto_error=False)

# FIX-2: bcrypt with random per-hash salt — replaces PBKDF2 with static JWT_SECRET salt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash password with bcrypt (random salt per hash, adaptive work factor)."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Constant-time bcrypt verification."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Short-lived access token (default 15 minutes) with unique JTI."""
    to_encode = data.copy()
    # FIX: timezone-aware UTC (datetime.utcnow() deprecated in Python 3.12+)
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    jti = str(uuid.uuid4())
    to_encode.update({"exp": expire, "type": "access", "jti": jti})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Long-lived refresh token (default 7 days) with unique JTI for HttpOnly cookie."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=7))
    jti = str(uuid.uuid4())
    to_encode.update({"exp": expire, "type": "refresh", "jti": jti})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


async def blacklist_jti(jti: str, ttl_seconds: int = 86400 * 7):
    """Blacklist a revoked JWT ID (jti) in Redis in O(1) time."""
    await redis_client.set(f"blacklist:{jti}", "revoked", ex=ttl_seconds)


async def is_jti_blacklisted(jti: str) -> bool:
    """O(1) Redis check for revoked JTI."""
    val = await redis_client.get(f"blacklist:{jti}")
    return val is not None


async def decode_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    """Decode and validate JWT token: signature, expiry, type, and Redis revocation list."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])

        if payload.get("type") != expected_type:
            raise HTTPException(status_code=401, detail=f"Invalid token type. Expected {expected_type}.")

        jti = payload.get("jti")
        if jti and await is_jti_blacklisted(jti):
            raise HTTPException(status_code=401, detail="Token has been revoked/blacklisted.")

        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> Dict[str, Any]:
    """
    FIX-3: Enforce authentication on all protected endpoints.
    Removed anonymous guest fallback — every unauthenticated request gets 401.
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await decode_token(credentials.credentials, expected_type="access")


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> Optional[Dict[str, Any]]:
    """
    Optional auth dependency for endpoints that accept both authenticated and anonymous users.
    Returns None (not a fake guest dict) when no token is provided.
    """
    if not credentials:
        return None
    try:
        return await decode_token(credentials.credentials, expected_type="access")
    except HTTPException:
        return None
