import logging
import asyncio
from typing import Optional, List
from app.core.database import db
from app.core.redis import redis_client
from app.core.metrics import CRDT_OPS_TOTAL

logger = logging.getLogger("nexagrid.crdt")

class CRDTService:
    """
    CRDT State & Snapshot Management Service (Y.js).
    Handles operation buffering in Redis, cross-node pub/sub broadcast,
    and compact document snapshot checkpoints into PostgreSQL every 50 ops.
    """
    SNAPSHOT_INTERVAL = 50

    async def process_update(self, room_id: str, update_bytes: bytes):
        # 1. Increment operational metrics
        CRDT_OPS_TOTAL.labels(room_id=room_id).inc()

        # 2. Push update binary to Redis room buffer
        ops_key = f"room:{room_id}:ops"
        await redis_client.lpush(ops_key, update_bytes)

        # 3. Publish binary update over Redis Pub/Sub for cross-node instance broadcast
        await redis_client.publish(f"room:{room_id}:updates", update_bytes)

        # 4. Check if snapshot checkpoint threshold is met
        op_count = await redis_client.llen(ops_key)
        if op_count >= self.SNAPSHOT_INTERVAL:
            asyncio.create_task(self.snapshot_document(room_id, op_count))

    async def snapshot_document(self, room_id: str, op_count: int):
        """Acquires Redis distributed lock to compact CRDT ops into DB snapshot."""
        lock_name = f"snapshot:{room_id}"
        acquired = await redis_client.acquire_lock(lock_name, timeout_ms=5000)
        if not acquired:
            return

        try:
            ops_key = f"room:{room_id}:ops"
            raw_ops = await redis_client.lrange(ops_key, 0, -1)
            if not raw_ops:
                return

            # Combine binary updates into single merged binary blob
            combined_snapshot = b"".join(raw_ops)

            # Persist checkpoint to PostgreSQL
            await db.execute(
                """INSERT INTO room_snapshots (room_id, snapshot_data, op_count)
                   VALUES ($1, $2, $3)""",
                room_id, combined_snapshot, op_count
            )
            logger.info(f"Snapshot created for room {room_id} at {op_count} ops.")
        except Exception as e:
            logger.error(f"Failed to create snapshot for room {room_id}: {e}")
        finally:
            await redis_client.release_lock(lock_name)

    async def get_latest_snapshot(self, room_id: str) -> Optional[bytes]:
        row = await db.fetchrow(
            """SELECT snapshot_data FROM room_snapshots
               WHERE room_id = $1 ORDER BY op_count DESC LIMIT 1""",
            room_id
        )
        if row:
            return row["snapshot_data"]
        return None

crdt_service = CRDTService()
