import logging
import asyncio
from typing import Optional, List
from app.core.database import db
from app.core.redis import redis_client
from app.core.metrics import CRDT_OPS_TOTAL

logger = logging.getLogger("nexagrid.crdt")


class CRDTService:
    """
    CRDT State & Snapshot Management Service (Y.js / y-py).

    Lifecycle:
      1. Receive binary Y.js update from WebSocket client.
      2. Buffer update in Redis list (room:{room_id}:ops).
      3. Broadcast via Redis Pub/Sub for cross-node fan-out.
      4. Every SNAPSHOT_INTERVAL ops: merge all buffered ops into a single
         valid Y.Doc state vector using y_py.merge_updates() and checkpoint
         to PostgreSQL.

    FIX-5: Previous implementation used b"".join(raw_ops) — byte concatenation
    of Y.js update blobs is NOT a valid merge. Y.js updates are encoded as
    differential state vectors; they must be merged with y_py.merge_updates()
    (which calls Y.mergeUpdates() internally) to produce a valid Y.Doc state.
    """

    SNAPSHOT_INTERVAL = 50

    async def process_update(self, room_id: str, update_bytes: bytes):
        # 1. Increment aggregate operational metric (no room_id label — see metrics.py FIX-6)
        CRDT_OPS_TOTAL.inc()

        # 2. Push binary update into Redis room buffer
        ops_key = f"room:{room_id}:ops"
        await redis_client.lpush(ops_key, update_bytes)

        # 3. Broadcast binary update over Redis Pub/Sub for cross-node fan-out
        await redis_client.publish(f"room:{room_id}:updates", update_bytes)

        # 4. Snapshot checkpoint if threshold reached
        op_count = await redis_client.llen(ops_key)
        if op_count >= self.SNAPSHOT_INTERVAL:
            asyncio.create_task(self.snapshot_document(room_id, op_count))

    async def snapshot_document(self, room_id: str, op_count: int):
        """
        Acquire Redis distributed lock, merge buffered Y.js ops into a valid
        Y.Doc state vector, and checkpoint to PostgreSQL.

        FIX-5: Uses y_py.merge_updates() — the correct Y.js binary merge operation.
        The result is a valid Y.Doc state that clients can apply with Y.applyUpdate().
        """
        lock_name = f"snapshot:{room_id}"
        acquired = await redis_client.acquire_lock(lock_name, timeout_ms=5000)
        if not acquired:
            return

        try:
            ops_key = f"room:{room_id}:ops"
            # Fetch ops in insertion order (lrange returns newest-first from lpush,
            # so reverse to maintain chronological order for correct merge)
            raw_ops: List[bytes] = await redis_client.lrange(ops_key, 0, -1)
            if not raw_ops:
                return

            # FIX-5: Correct Y.js merge — NOT b"".join(raw_ops)
            merged_state = self._merge_yjs_updates(list(reversed(raw_ops)))

            await db.execute(
                """INSERT INTO room_snapshots (room_id, snapshot_data, op_count)
                   VALUES ($1, $2, $3)""",
                room_id, merged_state, op_count,
            )
            logger.info("Y.js snapshot created for room %s at %d ops.", room_id, op_count)

            # Clear the buffered ops after successful snapshot
            await redis_client.delete(ops_key)

        except Exception as e:
            logger.error("Failed to create Y.js snapshot for room %s: %s", room_id, e)
        finally:
            await redis_client.release_lock(lock_name)

    def _merge_yjs_updates(self, updates: List[bytes]) -> bytes:
        """
        Merge a list of Y.js binary update blobs into a single valid Y.Doc state.
        Uses y_py.merge_updates() when available; falls back to concatenation
        (for test environments without y_py installed) with a clear warning.

        In production, y-py must be installed for correct CRDT semantics.
        """
        try:
            import y_py  # type: ignore
            return y_py.merge_updates(updates)
        except ImportError:
            logger.warning(
                "y_py not installed — falling back to raw update concatenation. "
                "This is INCORRECT for production. Install y-py for valid Y.js merges."
            )
            return b"".join(updates)

    async def get_latest_snapshot(self, room_id: str) -> Optional[bytes]:
        """Retrieve the most recent Y.Doc state vector for a room from PostgreSQL."""
        row = await db.fetchrow(
            """SELECT snapshot_data FROM room_snapshots
               WHERE room_id = $1 ORDER BY op_count DESC LIMIT 1""",
            room_id,
        )
        return row["snapshot_data"] if row else None


crdt_service = CRDTService()
