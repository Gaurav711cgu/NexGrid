import uuid
import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.core.redis import redis_client

security_bearer = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    """Hash password securely using PBKDF2 SHA-256 with salt."""
    salt = settings.JWT_SECRET[:16]
    return hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Short-lived access token (default 15 minutes) with unique JTI."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    jti = str(uuid.uuid4())
    to_encode.update({
        "exp": expire,
        "type": "access",
        "jti": jti
    })
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Long-lived refresh token (default 7 days) with unique JTI for HttpOnly cookie."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=7))
    jti = str(uuid.uuid4())
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "jti": jti
    })
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

async def blacklist_jti(jti: str, ttl_seconds: int = 86400 * 7):
    """Blacklist a revoked JWT ID (jti) in Redis in O(1) time."""
    await redis_client.set(f"blacklist:{jti}", "revoked", ex=ttl_seconds)

async def is_jti_blacklisted(jti: str) -> bool:
    """Check if JTI is in Redis revocation list."""
    val = await redis_client.get(f"blacklist:{jti}")
    return val is not None

async def decode_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    """Decode and validate JWT token checking signature, expiry, type, and Redis revocation list."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        
        # Validate token type
        if payload.get("type") != expected_type:
            raise HTTPException(status_code=401, detail=f"Invalid token type. Expected {expected_type}.")
        
        # Check Redis revocation blacklist
        jti = payload.get("jti")
        if jti and await is_jti_blacklisted(jti):
            raise HTTPException(status_code=401, detail="Token has been revoked/blacklisted.")
            
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)) -> Dict[str, Any]:
    if not credentials:
        # Development anonymous fallback if no bearer header passed
        return {"id": "00000000-0000-0000-0000-000000000000", "email": "guest@nexagrid.dev", "display_name": "Guest Engineer"}
    return await decode_token(credentials.credentials, expected_type="access")
