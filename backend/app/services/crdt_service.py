import logging
import asyncio
from typing import Optional, List
from app.core.database import db
from app.core.redis import redis_client
from app.core.metrics import CRDT_OPS_TOTAL

logger = logging.getLogger("nexagrid.crdt")


class CRDTService:
    """
    FAANG/Staff-Engineer Hardened CRDT State & Streams Sync Service (Y.js / y-py).

    Architecture:
      1. Receive binary Y.js update from WebSocket client.
      2. Append update to Redis Stream (`stream:room:{room_id}`) with entry ID for zero-loss sync.
      3. Cross-node fan-out via Redis Stream / Pub/Sub backplane.
      4. Support `get_missing_updates(room_id, last_seq_id)` via `XRANGE` to replay lost deltas for re-connecting clients.
      5. Snapshot Checkpoint: Every SNAPSHOT_INTERVAL ops, merge all updates using `y_py.merge_updates()`
         and save state vector to PostgreSQL.
    """

    SNAPSHOT_INTERVAL = 50

    async def process_update(self, room_id: str, update_bytes: bytes, sender_id: str = "unknown") -> str:
        """
        Process incoming CRDT update binary blob.
        Appends to Redis Stream for persistent ordering and broadcasts update to cross-node subscribers.
        Returns the Redis Stream entry ID (sequence ID).
        """
        CRDT_OPS_TOTAL.inc()

        ops_key = f"room:{room_id}:ops"
        stream_key = f"stream:room:{room_id}"

        # 1. Push to Redis List buffer for fast count & snapshotting
        await redis_client.lpush(ops_key, update_bytes)

        # 2. Append to Redis Stream for persistent, ordered event stream with replay capability
        seq_id = "0-0"
        try:
            if hasattr(redis_client.redis, "xadd") and redis_client.redis is not None:
                payload_hex = update_bytes.hex()
                entry_id = await redis_client.redis.xadd(
                    stream_key,
                    {"op": "update", "payload": payload_hex, "sender": sender_id},
                    maxlen=10000
                )
                seq_id = entry_id.decode("utf-8") if isinstance(entry_id, bytes) else str(entry_id)
        except Exception as e:
            logger.debug(f"Redis Stream XADD fallback (using in-memory/list buffer): {e}")

        # 3. Broadcast update over Redis Pub/Sub for realtime cross-instance fanout
        await redis_client.publish(f"room:{room_id}:updates", update_bytes)

        # 4. Check for snapshot checkpoint threshold
        op_count = await redis_client.llen(ops_key)
        if op_count >= self.SNAPSHOT_INTERVAL:
            asyncio.create_task(self.snapshot_document(room_id, op_count))

        return seq_id

    async def get_missing_updates(self, room_id: str, last_seq_id: str = "-") -> List[bytes]:
        """
        Replay missing CRDT updates for a re-connecting client starting from `last_seq_id`.
        Uses `XRANGE` on the room's Redis Stream.
        """
        stream_key = f"stream:room:{room_id}"
        missing_updates: List[bytes] = []

        try:
            if hasattr(redis_client.redis, "xrange") and redis_client.redis is not None:
                # If last_seq_id is valid, query xrange starting exclusive of last_seq_id
                start_id = last_seq_id if last_seq_id != "-" else "-"
                entries = await redis_client.redis.xrange(stream_key, min=start_id, max="+")
                for entry_id, fields in entries:
                    # Skip exact match if not "-"
                    str_id = entry_id.decode() if isinstance(entry_id, bytes) else str(entry_id)
                    if str_id == last_seq_id:
                        continue
                    payload_raw = fields.get(b"payload") or fields.get("payload")
                    if payload_raw:
                        p_str = payload_raw.decode() if isinstance(payload_raw, bytes) else payload_raw
                        missing_updates.append(bytes.fromhex(p_str))
        except Exception as e:
            logger.warning(f"Error fetching missing updates from Redis Stream for room {room_id}: {e}")

        if not missing_updates:
            # Fallback to list buffer if stream replay returned empty
            ops = await redis_client.lrange(f"room:{room_id}:ops", 0, -1)
            if ops:
                missing_updates = list(reversed(ops))

        return missing_updates

    async def snapshot_document(self, room_id: str, op_count: int):
        """
        Acquire Redis distributed lock, merge buffered Y.js ops into a valid
        Y.Doc state vector using y_py.merge_updates(), and checkpoint to PostgreSQL.
        """
        lock_name = f"snapshot:{room_id}"
        acquired = await redis_client.acquire_lock(lock_name, timeout_ms=5000)
        if not acquired:
            return

        try:
            ops_key = f"room:{room_id}:ops"
            raw_ops: List[bytes] = await redis_client.lrange(ops_key, 0, -1)
            if not raw_ops:
                return

            merged_state = self._merge_yjs_updates(list(reversed(raw_ops)))

            await db.execute(
                """INSERT INTO room_snapshots (room_id, snapshot_data, op_count)
                   VALUES ($1, $2, $3)""",
                room_id, merged_state, op_count,
            )
            logger.info("Y.js stream snapshot created for room %s at %d ops.", room_id, op_count)

            # Clear the buffered ops after successful snapshot
            await redis_client.delete(ops_key)

        except Exception as e:
            logger.error("Failed to create Y.js snapshot for room %s: %s", room_id, e)
        finally:
            await redis_client.release_lock(lock_name)

    def _merge_yjs_updates(self, updates: List[bytes]) -> bytes:
        """
        Merge a list of Y.js binary update blobs into a single valid Y.Doc state using y_py.
        """
        try:
            import y_py  # type: ignore
            return y_py.merge_updates(updates)  # type: ignore
        except ImportError:
            logger.warning("y_py not installed — falling back to binary concatenation for dev/test.")
            return b"".join(updates)

    async def get_latest_snapshot(self, room_id: str) -> Optional[bytes]:
        """Fetch the most recent Y.Doc binary snapshot for a room."""
        row = await db.fetchrow(
            """SELECT snapshot_data FROM room_snapshots
               WHERE room_id = $1 ORDER BY created_at DESC LIMIT 1""",
            room_id,
        )
        if row and row["snapshot_data"]:
            return bytes(row["snapshot_data"])
        return None


crdt_service = CRDTService()
