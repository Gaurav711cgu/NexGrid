import uuid
import json
import hashlib
import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.models.schemas import ExecuteCodeRequest, ExecutionResult
from app.auth.security import get_current_user
from app.services.sandbox_service import sandbox_engine
from app.services.rate_limiter import rate_limiter
from app.services.ai_service import ai_service
from app.core.database import db

router = APIRouter(prefix="/execution", tags=["Execution"])

class DebugErrorRequest(BaseModel):
    code: str
    stderr: str
    language: str = "python"

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

    # 3. Log to PostgreSQL asynchronously (out-of-band execution log insertion prevents DB connection pool contention)
    exec_id = str(uuid.uuid4())
    code_hash = hashlib.sha256(req.code.encode('utf-8')).hexdigest()
    
    async def log_execution_background():
        try:
            await db.execute(
                """INSERT INTO execution_logs (id, room_id, user_id, language, code_hash, stdout, stderr, exit_code, execution_time_ms, blocked, metadata, executed_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)""",
                exec_id, room_id, user["id"], req.language, code_hash,
                result.stdout, result.stderr, result.exit_code, result.execution_time_ms,
                True if result.blocked else False, json.dumps(result.metadata), datetime.now(timezone.utc).isoformat()
            )
        except Exception:
            pass

    asyncio.create_task(log_execution_background())

    return result

@router.post("/{room_id}/debug")
async def debug_execution_error(
    room_id: str,
    req: DebugErrorRequest,
    user: dict = Depends(get_current_user)
):
    """
    AI Automated Error Debugging Endpoint.
    Analyzes code + error traceback and streams diagnosis token-by-token.
    """
    async def event_generator():
        async for chunk in ai_service.stream_completion(
            action="fix_error",
            code=req.code,
            language=req.language,
            context=req.stderr
        ):
            yield chunk

    return StreamingResponse(event_generator(), media_type="text/plain")
