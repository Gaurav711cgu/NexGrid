import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import RegisterRequest, LoginRequest, AuthResponse
from app.auth.security import hash_password, verify_password, create_access_token, get_current_user
from app.core.database import db

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(req: RegisterRequest):
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
    token = create_access_token(user_data)
    return AuthResponse(access_token=token, user=user_data)

@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    user = await db.fetchrow("SELECT * FROM users WHERE email = $1", req.email)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_data = {"id": str(user["id"]), "email": user["email"], "display_name": user["display_name"]}
    token = create_access_token(user_data)
    return AuthResponse(access_token=token, user=user_data)

@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {"user": user}
