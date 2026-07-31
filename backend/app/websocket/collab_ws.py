import logging
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.crdt_service import crdt_service
from app.core.metrics import WS_CONNECTIONS_ACTIVE
from app.core.redis import redis_client

logger = logging.getLogger("nexagrid.ws_collab")
router = APIRouter()

# Active connection store per room
room_connections = {}

@router.websocket("/rooms/{room_id}/collab")
async def collaboration_websocket(websocket: WebSocket, room_id: str):
    await websocket.accept()
    
    if room_id not in room_connections:
        room_connections[room_id] = set()
    room_connections[room_id].add(websocket)
    WS_CONNECTIONS_ACTIVE.labels(room_id=room_id).set(len(room_connections[room_id]))

    # Send current document snapshot on join if available
    latest_snapshot = await crdt_service.get_latest_snapshot(room_id)
    if latest_snapshot:
        await websocket.send_bytes(latest_snapshot)

    try:
        while True:
            # Receive binary Y.js CRDT delta update from client
            data = await websocket.receive_bytes()
            if not data:
                continue

            # Process CRDT update, buffer in Redis & snapshot if threshold reached
            await crdt_service.process_update(room_id, data)

            # Broadcast binary update to all other connected room clients
            for client in list(room_connections.get(room_id, [])):
                if client != websocket:
                    try:
                        await client.send_bytes(data)
                    except Exception:
                        pass

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected from collab room {room_id}")
    except Exception as e:
        logger.error(f"WebSocket error in room {room_id}: {e}")
    finally:
        if room_id in room_connections:
            room_connections[room_id].discard(websocket)
            WS_CONNECTIONS_ACTIVE.labels(room_id=room_id).set(len(room_connections[room_id]))
