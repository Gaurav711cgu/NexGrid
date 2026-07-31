import uuid
import json
import hashlib
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import ExecuteCodeRequest, ExecutionResult
from app.auth.security import get_current_user
from app.services.sandbox_service import sandbox_engine
from app.services.rate_limiter import rate_limiter
from app.core.database import db

router = APIRouter(prefix="/execution", tags=["Execution"])

@router.post("/{room_id}/run", response_model=ExecutionResult)
async def execute_code_in_room(
    room_id: str,
    req: ExecuteCodeRequest,
    user: dict = Depends(get_current_user)
):
    # 1. Rate Limiting Check
    allowed, remaining = await rate_limiter.is_allowed(f"exec:{user['id']}")
    if not allowed:
        raise HTTPException(status_code=429, detail="Execution rate limit exceeded. Please wait a moment.")

    # 2. Execute Code in Sandbox Engine
    result = await sandbox_engine.execute(
        code=req.code,
        language=req.language,
        stdin=req.stdin
    )

    # 3. Log to PostgreSQL with JSONB Telemetry Data
    exec_id = str(uuid.uuid4())
    code_hash = hashlib.sha256(req.code.encode('utf-8')).hexdigest()
    
    await db.execute(
        """INSERT INTO execution_logs (id, room_id, user_id, language, code_hash, stdout, stderr, exit_code, execution_time_ms, blocked, metadata, executed_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)""",
        exec_id, room_id, user["id"], req.language, code_hash,
        result.stdout, result.stderr, result.exit_code, result.execution_time_ms,
        1 if result.blocked else 0, json.dumps(result.metadata), datetime.utcnow().isoformat()
    )

    return result
