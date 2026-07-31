import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.crdt_service import crdt_service
from app.core.metrics import WS_CONNECTIONS_ACTIVE
from app.core.redis import redis_client

logger = logging.getLogger("nexagrid.ws_collab")
router = APIRouter()

room_connections: dict[str, set[WebSocket]] = {}

@router.websocket("/rooms/{room_id}/collab")
async def collaboration_websocket(websocket: WebSocket, room_id: str):
    await websocket.accept()

    if room_id not in room_connections:
        room_connections[room_id] = set()
    room_connections[room_id].add(websocket)
    WS_CONNECTIONS_ACTIVE.labels(room_id=room_id).set(len(room_connections[room_id]))

    # Send current snapshot on join
    latest_snapshot = await crdt_service.get_latest_snapshot(room_id)
    if latest_snapshot:
        await websocket.send_bytes(latest_snapshot)

    # Subscribe to Redis Pub/Sub for cross-node broadcast
    channel = f"room:{room_id}:updates"
    redis_queue = redis_client.fallback.subscribe(channel) if redis_client.use_fallback else None

    async def redis_listener():
        """Reads from Redis channel and broadcasts to local WebSocket connections."""
        try:
            if redis_queue:
                while True:
                    message = await redis_queue.get()
                    if message is None:
                        break
                    for client in list(room_connections.get(room_id, [])):
                        if client != websocket:
                            try:
                                await client.send_bytes(message)
                            except Exception:
                                pass
        except asyncio.CancelledError:
            pass

    listener_task = asyncio.create_task(redis_listener())

    try:
        while True:
            data = await websocket.receive_bytes()
            if not data:
                continue
            # Process update & publish to Redis Pub/Sub
            await crdt_service.process_update(room_id, data)

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from room {room_id}")
    finally:
        listener_task.cancel()
        if redis_queue:
            redis_client.fallback.unsubscribe(channel, redis_queue)
        if room_id in room_connections:
            room_connections[room_id].discard(websocket)
            WS_CONNECTIONS_ACTIVE.labels(room_id=room_id).set(
                len(room_connections[room_id])
            )
