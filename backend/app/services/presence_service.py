import json
import time
import hashlib
from typing import Dict, Any, List
from app.core.redis import redis_client
from app.core.metrics import ROOM_PARTICIPANT_COUNT

COLORS = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#6C5CE7", "#FD79A8"]

class PresenceManager:
    """
    Tracks online room presence, deterministic colors, active user counts,
    and cursor line/column coordinates in Redis hashes.
    """
    def _assign_color(self, user_id: str) -> str:
        idx = int(hashlib.md5(user_id.encode('utf-8')).hexdigest(), 16) % len(COLORS)
        return COLORS[idx]

    async def join_room(self, room_id: str, user_id: str, display_name: str) -> Dict[str, Any]:
        presence = {
            "user_id": user_id,
            "display_name": display_name,
            "cursor_line": 1,
            "cursor_col": 1,
            "color": self._assign_color(user_id),
            "joined_at": time.time()
        }
        key = f"presence:{room_id}"
        await redis_client.hset(key, user_id, json.dumps(presence))
        count = await redis_client.hlen(key)
        ROOM_PARTICIPANT_COUNT.labels(room_id=room_id).set(count)
        return presence

    async def update_cursor(self, room_id: str, user_id: str, line: int, col: int) -> Dict[str, Any]:
        key = f"presence:{room_id}"
        raw = await redis_client.get(f"presence_raw:{room_id}:{user_id}")
        data = json.loads(raw) if raw else {"user_id": user_id, "color": self._assign_color(user_id)}
        data["cursor_line"] = line
        data["cursor_col"] = col
        await redis_client.hset(key, user_id, json.dumps(data))
        return data

    async def leave_room(self, room_id: str, user_id: str):
        key = f"presence:{room_id}"
        await redis_client.hdel(key, user_id)
        count = await redis_client.hlen(key)
        ROOM_PARTICIPANT_COUNT.labels(room_id=room_id).set(count)

    async def get_room_presence(self, room_id: str) -> List[Dict[str, Any]]:
        key = f"presence:{room_id}"
        raw_dict = await redis_client.hgetall(key)
        res = []
        for _, val in raw_dict.items():
            try:
                res.append(json.loads(val.decode('utf-8') if isinstance(val, bytes) else val))
            except Exception:
                pass
        return res

presence_manager = PresenceManager()
