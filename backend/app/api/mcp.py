from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.services.sandbox_service import sandbox_engine
from app.core.database import db
from app.api.rooms import create_room, CreateRoomRequest
# FIX-4: Import real auth dependency — MCP endpoints now require a valid bearer token
from app.auth.security import get_current_user

router = APIRouter(prefix="/mcp", tags=["MCP Server"])


class MCPToolCallRequest(BaseModel):
    name: str
    arguments: Optional[Dict[str, Any]] = {}


@router.post("/tools/list")
async def list_mcp_tools():
    """
    Model Context Protocol (MCP) Tool Registry endpoint.
    Exposes NexaGrid system capabilities to AI agents and external tools.
    Note: listing tools is public; executing tools requires authentication.
    """
    return {
        "tools": [
            {
                "name": "nexgrid_create_room",
                "description": "Create a new real-time collaborative coding room and return join code & URL.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Room name"},
                        "language": {
                            "type": "string",
                            "description": "Target language (python, javascript, go, rust, java)",
                        },
                    },
                    "required": ["name"],
                },
            },
            {
                "name": "nexgrid_execute_sandbox",
                "description": "Execute code snippet inside POSIX-isolated sandbox with resource limits.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code string to execute"},
                        "language": {
                            "type": "string",
                            "description": "Target language (python, javascript, go, rust, java)",
                        },
                        "stdin": {"type": "string", "description": "Optional stdin string"},
                    },
                    "required": ["code", "language"],
                },
            },
            {
                "name": "nexgrid_get_analytics",
                "description": "Retrieve SQL analytical telemetry metrics (window functions) for a room.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "room_id": {"type": "string", "description": "UUID room ID"}
                    },
                    "required": ["room_id"],
                },
            },
        ]
    }


@router.post("/tools/execute")
async def execute_mcp_tool(
    request: MCPToolCallRequest,
    # FIX-4: Removed hardcoded user={"id": "mcp-agent", ...} — now requires real auth
    user: dict = Depends(get_current_user),
):
    """
    Execute a specific MCP tool by name.
    FIX-4: Authentication required. The real authenticated user is passed to room creation,
    ensuring owner_id foreign key references a real user in the users table.
    """
    tool_name = request.name
    args = request.arguments or {}

    if tool_name == "nexgrid_create_room":
        name = args.get("name", "MCP Collaborative Workspace")
        language = args.get("language", "python")
        room_req = CreateRoomRequest(name=name, language=language)
        # Pass the real authenticated user from the JWT token — no more fake IDs
        result = await create_room(room_req, user=user)
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Room created successfully! Code: {result['code']}, Join URL: /rooms/{result['code']}",
                }
            ],
            "room": result,
        }

    elif tool_name == "nexgrid_execute_sandbox":
        code = args.get("code", "")
        language = args.get("language", "python")
        stdin = args.get("stdin")
        res = await sandbox_engine.execute(code=code, language=language, stdin=stdin)
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Execution finished with exit code {res.exit_code}.\nStdout:\n{res.stdout}\nStderr:\n{res.stderr}",
                }
            ],
            "result": res.dict(),
        }

    elif tool_name == "nexgrid_get_analytics":
        room_id = args.get("room_id")
        if not room_id:
            raise HTTPException(status_code=400, detail="room_id argument is required")
        query = """
        SELECT language, COUNT(*) AS total_executions,
               ROUND(AVG(execution_time_ms)::numeric, 2) AS avg_latency_ms
        FROM execution_logs WHERE room_id = $1 GROUP BY language;
        """
        rows = await db.fetch(query, room_id)
        return {
            "content": [{"type": "text", "text": f"Analytics for room {room_id}: {rows}"}],
            "analytics": rows,
        }

    else:
        raise HTTPException(status_code=404, detail=f"MCP tool '{tool_name}' not found.")
