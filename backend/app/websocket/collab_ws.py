import asyncio
import logging
from typing import Optional, Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from app.services.crdt_service import crdt_service
from app.core.metrics import WS_CONNECTIONS_ACTIVE
from app.core.redis import redis_client
from app.auth.security import decode_token

logger = logging.getLogger("nexagrid.ws_collab")
router = APIRouter()

# Multi-tenant per-room connection & client queue registry
room_connections: Dict[str, Set[WebSocket]] = {}
client_queues: Dict[WebSocket, asyncio.Queue] = {}


@router.websocket("/rooms/{room_id}/collab")
async def collaboration_websocket(
    websocket: WebSocket,
    room_id: str,
    token: Optional[str] = None
):
    # 1. Level-4 Handshake Authentication (Token Query Param or Sec-WebSocket-Protocol)
    auth_token = token or websocket.query_params.get("token")
    if not auth_token:
        # Check subprotocols if token missing in query params
        subprotocols = websocket.headers.get("sec-websocket-protocol", "").split(",")
        for sub in subprotocols:
            sub_clean = sub.strip()
            if sub_clean.startswith("token."):
                auth_token = sub_clean[6:]
                break

    # Accept connection & validate payload
    await websocket.accept()

    user_info = None
    if auth_token:
        user_info = decode_token(auth_token)
        if not user_info:
            logger.warning(f"Unauthorized WebSocket connection attempt to room {room_id}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or expired token")
            return

    # 2. Register connection & initialize Per-Client Bounded Buffer Queue for Slow Consumer Backpressure
    if room_id not in room_connections:
        room_connections[room_id] = set()
    room_connections[room_id].add(websocket)
    WS_CONNECTIONS_ACTIVE.labels(room_id=room_id).set(len(room_connections[room_id]))

    # Bounded queue (max 100 frames) prevents slow 3G clients from blocking fast peers
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    client_queues[websocket] = queue

    # Dedicated per-client writer task
    async def client_writer():
        try:
            while True:
                msg_bytes = await queue.get()
                await websocket.send_bytes(msg_bytes)
                queue.task_done()
        except (asyncio.CancelledError, WebSocketDisconnect, Exception):
            pass

    writer_task = asyncio.create_task(client_writer())

    # 3. Send latest Y.js snapshot on join
    latest_snapshot = await crdt_service.get_latest_snapshot(room_id)
    if latest_snapshot:
        try:
            queue.put_nowait(latest_snapshot)
        except asyncio.QueueFull:
            pass

    # 4. Redis Pub/Sub Subscriber Listener Task
    channel = f"room:{room_id}:updates"
    redis_queue = redis_client.fallback.subscribe(channel) if redis_client.use_fallback else None

    async def redis_listener():
        """Reads from Redis channel and dispatches asynchronously to per-client queue buffers."""
        try:
            if redis_queue:
                while True:
                    message = await redis_queue.get()
                    if message is None:
                        break
                    for client in list(room_connections.get(room_id, [])):
                        if client != websocket:
                            c_queue = client_queues.get(client)
                            if c_queue:
                                try:
                                    # Non-blocking enqueue prevents slow consumers from blocking room loop
                                    c_queue.put_nowait(message)
                                except asyncio.QueueFull:
                                    logger.warning(f"Slow consumer detected in room {room_id}. Dropping overflow frame.")
        except asyncio.CancelledError:
            pass

    listener_task = asyncio.create_task(redis_listener())

    try:
        while True:
            data = await websocket.receive_bytes()
            if not data:
                continue
            sender = user_info.get("sub", "anonymous") if user_info else "anonymous"
            await crdt_service.process_update(room_id, data, sender_id=sender)

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from room {room_id}")
    finally:
        listener_task.cancel()
        writer_task.cancel()
        if redis_queue:
            redis_client.fallback.unsubscribe(channel, redis_queue)
        client_queues.pop(websocket, None)
        if room_id in room_connections:
            room_connections[room_id].discard(websocket)
            WS_CONNECTIONS_ACTIVE.labels(room_id=room_id).set(len(room_connections[room_id]))
