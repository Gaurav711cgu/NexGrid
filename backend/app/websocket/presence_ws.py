import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.presence_service import presence_manager

from typing import Dict, Optional

logger = logging.getLogger("nexagrid.ws_presence")
router = APIRouter()

presence_connections: Dict[str, Dict[str, WebSocket]] = {}

@router.websocket("/rooms/{room_id}/presence")
async def presence_websocket(websocket: WebSocket, room_id: str):
    await websocket.accept()

    user_id = f"user_{id(websocket)}"
    display_name = f"User {user_id[-4:]}"

    if room_id not in presence_connections:
        presence_connections[room_id] = {}
    presence_connections[room_id][user_id] = websocket

    user_presence = await presence_manager.join_room(room_id, user_id, display_name)

    # Broadcast join event to all room participants
    await broadcast_presence_event(room_id, {
        "type": "user_joined",
        "user": user_presence,
        "all_users": await presence_manager.get_room_presence(room_id)
    })

    try:
        while True:
            data_text = await websocket.receive_text()
            data = json.loads(data_text)
            msg_type = data.get("type")

            if msg_type == "cursor_update":
                line = data.get("line", 1)
                col = data.get("col", 1)
                updated = await presence_manager.update_cursor(room_id, user_id, line, col)
                
                await broadcast_presence_event(room_id, {
                    "type": "cursor_update",
                    "user_id": user_id,
                    "line": line,
                    "col": col,
                    "color": updated.get("color", "#6366f1")
                }, exclude_user=user_id)

    except WebSocketDisconnect:
        logger.info(f"Presence WebSocket client disconnected from room {room_id}")
    except Exception as e:
        logger.error(f"Presence WebSocket error: {e}")
    finally:
        await presence_manager.leave_room(room_id, user_id)
        if room_id in presence_connections:
            presence_connections[room_id].pop(user_id, None)

        await broadcast_presence_event(room_id, {
            "type": "user_left",
            "user_id": user_id,
            "all_users": await presence_manager.get_room_presence(room_id)
        })

async def broadcast_presence_event(room_id: str, message: dict, exclude_user: Optional[str] = None):
    if room_id not in presence_connections:
        return
    for uid, ws in list(presence_connections[room_id].items()):
        if uid != exclude_user:
            try:
                await ws.send_json(message)
            except Exception:
                pass
