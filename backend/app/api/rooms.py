import uuid
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from app.models.schemas import CreateRoomRequest, RoomResponse, PaginatedExecutionLogs
from app.auth.security import get_current_user
from app.core.database import db

router = APIRouter(prefix="/rooms", tags=["Rooms"])

BOILERPLATE = {
    "python": "def solution():\n    print('Hello from NexaGrid real-time collaboration!')\n\nsolution()\n",
    "javascript": "function solution() {\n    console.log('Hello from NexaGrid real-time collaboration!');\n}\n\nsolution();\n",
    "go": "package main\n\nimport \"fmt\"\n\nfunc main() {\n    fmt.Println(\"Hello from NexaGrid real-time collaboration!\")\n}\n",
    "rust": "fn main() {\n    println!(\"Hello from NexaGrid real-time collaboration!\");\n}\n",
    "java": "public class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello from NexaGrid real-time collaboration!\");\n    }\n}\n"
}

class RecordEventRequest(BaseModel):
    seq_num: int
    event_type: str = "crdt_update"
    payload: str

@router.post("", response_model=RoomResponse, status_code=201)
async def create_room(req: CreateRoomRequest, user: dict = Depends(get_current_user)):
    room_id = uuid.uuid4()
    code = secrets.token_urlsafe(4).upper()[:6]
    lang = (req.language or "python").lower()
    initial_code = req.initial_code or BOILERPLATE.get(lang, BOILERPLATE["python"])
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=req.duration_hours or 24)
    name = req.name or f"Room {code}"

    await db.execute(
        """INSERT INTO rooms (id, code, name, language, owner_id, expires_at, max_participants, is_public, initial_code)
           VALUES ($1::uuid, $2, $3, $4, $5::uuid, $6, $7, $8, $9)""",
        room_id, code, name, lang, uuid.UUID(user["id"]), expires_at, req.max_participants or 10, req.is_public or False, initial_code
    )

    return RoomResponse(
        id=str(room_id),
        code=code,
        name=name,
        language=lang,
        owner_id=str(user["id"]),
        created_at=now.isoformat(),
        expires_at=expires_at.isoformat(),
        max_participants=req.max_participants or 10,
        is_public=req.is_public or False,
        initial_code=initial_code
    )

@router.get("/{code}", response_model=RoomResponse)
async def get_room_by_code(code: str, user: dict = Depends(get_current_user)):
    room = await db.fetchrow("SELECT * FROM rooms WHERE code = $1", code.upper())
    if not room:
        raise HTTPException(status_code=404, detail="Room not found or expired")
    return RoomResponse(
        id=str(room["id"]),
        code=room["code"],
        name=room["name"],
        language=room["language"],
        owner_id=str(room["owner_id"]) if room["owner_id"] else None,
        created_at=str(room["created_at"]),
        expires_at=str(room["expires_at"]),
        max_participants=room["max_participants"],
        is_public=bool(room["is_public"]),
        initial_code=room["initial_code"] or ""
    )

@router.post("/{room_id}/events")
async def record_room_event(
    room_id: str,
    req: RecordEventRequest,
    user: dict = Depends(get_current_user)
):
    """
    Session Recording Engine: Records CRDT operation events for session playback.
    """
    event_id = uuid.uuid4()
    await db.execute(
        """INSERT INTO room_events (id, room_id, seq_num, event_type, payload, created_at)
           VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6)""",
        event_id, uuid.UUID(room_id), req.seq_num, req.event_type, req.payload, datetime.now(timezone.utc)
    )
    return {"status": "recorded", "event_id": event_id, "seq_num": req.seq_num}

@router.get("/{room_id}/replay")
async def get_room_replay(
    room_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Session Playback Engine: Fetches ordered CRDT operation sequence for session playback.
    """
    rows = await db.fetch(
        "SELECT id, room_id, seq_num, event_type, payload, created_at FROM room_events WHERE room_id = $1::uuid ORDER BY seq_num ASC",
        uuid.UUID(room_id)
    )
    return {
        "room_id": room_id,
        "total_events": len(rows),
        "events": [
            {
                "id": str(r["id"]),
                "seq_num": r["seq_num"],
                "event_type": r["event_type"],
                "payload": r["payload"],
                "created_at": str(r["created_at"])
            }
            for r in rows
        ]
    }

@router.get("/{room_id}/history", response_model=PaginatedExecutionLogs)
async def get_room_execution_history(
    room_id: str,
    cursor: Optional[str] = Query(None, description="Cursor for O(1) pagination (executed_at_id)"),
    limit: int = Query(10, ge=1, le=50),
    user: dict = Depends(get_current_user)
):
    """
    Advanced FAANG Pattern: Cursor-based pagination replacing OFFSET/LIMIT.
    Uses composite cursor index (executed_at DESC, id DESC).
    """
    if cursor:
        try:
            parts = cursor.split("_")
            cursor_time = parts[0]
            cursor_id = parts[1]
            query = """
                SELECT id, room_id, user_id, language, stdout, stderr, exit_code, execution_time_ms, blocked, metadata, executed_at
                FROM execution_logs
                WHERE room_id = $1::uuid AND (executed_at, id) < ($2, $3::uuid)
                ORDER BY executed_at DESC, id DESC
                LIMIT $4
            """
            rows = await db.fetch(query, uuid.UUID(room_id), cursor_time, uuid.UUID(cursor_id), limit + 1)
        except Exception:
            rows = []
    else:
        query = """
            SELECT id, room_id, user_id, language, stdout, stderr, exit_code, execution_time_ms, blocked, metadata, executed_at
            FROM execution_logs
            WHERE room_id = $1::uuid
            ORDER BY executed_at DESC, id DESC
            LIMIT $2
        """
        rows = await db.fetch(query, uuid.UUID(room_id), limit + 1)

    has_more = len(rows) > limit
    items = rows[:limit]
    
    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = f"{last['executed_at']}_{last['id']}"

    return PaginatedExecutionLogs(
        items=[{
            "id": str(r["id"]),
            "room_id": str(r["room_id"]),
            "user_id": str(r["user_id"]) if r["user_id"] else None,
            "language": r["language"],
            "stdout": r["stdout"],
            "stderr": r["stderr"],
            "exit_code": r["exit_code"],
            "execution_time_ms": r["execution_time_ms"],
            "blocked": bool(r["blocked"]),
            "metadata": r["metadata"] if isinstance(r["metadata"], dict) else {},
            "executed_at": str(r["executed_at"])
        } for r in items],
        next_cursor=next_cursor,
        has_more=has_more
    )
