import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.ai_service import ai_service

logger = logging.getLogger("nexagrid.ws_ai")
router = APIRouter()

@router.websocket("/rooms/{room_id}/ai-stream")
async def ai_stream_websocket(websocket: WebSocket, room_id: str):
    await websocket.accept()

    try:
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)

            action = data.get("action", "complete")
            code = data.get("code", "")
            language = data.get("language", "python")
            cursor_line = data.get("cursor_line", 0)
            context = data.get("context", "")

            # Stream response token by token
            async for token in ai_service.stream_completion(
                action=action,
                code=code,
                language=language,
                cursor_line=cursor_line,
                context=context
            ):
                await websocket.send_json({
                    "type": "token",
                    "delta": token
                })

            await websocket.send_json({"type": "complete"})

    except WebSocketDisconnect:
        logger.info(f"AI WebSocket client disconnected from room {room_id}")
    except Exception as e:
        logger.error(f"AI WebSocket error: {e}")
