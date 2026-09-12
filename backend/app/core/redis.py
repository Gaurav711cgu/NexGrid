import logging
import asyncio
from typing import Dict, Any, List, Set, Optional
from collections import defaultdict
from app.core.config import settings

logger = logging.getLogger("nexagrid.redis")

class InMemoryRedisFallback:
    """In-memory Redis fallback broker for development/testing when Redis server is unavailable."""
    def __init__(self):
        self.hashes: Dict[str, Dict[str, str]] = defaultdict(dict)
        self.lists: Dict[str, List[bytes]] = defaultdict(list)
        self.keys: Dict[str, Any] = {}
        self.listeners: Dict[str, Set[asyncio.Queue]] = defaultdict(set)
        self.locks: Set[str] = set()

    async def hset(self, key: str, field: str, value: str):
        self.hashes[key][field] = value

    async def hget(self, key: str, field: str) -> Optional[str]:
        return self.hashes[key].get(field)

    async def hgetall(self, key: str) -> Dict[str, str]:
        return self.hashes[key]

    async def hdel(self, key: str, field: str):
        self.hashes[key].pop(field, None)

    async def hlen(self, key: str) -> int:
        return len(self.hashes[key])

    async def lpush(self, key: str, value: bytes):
        self.lists[key].insert(0, value)

    async def llen(self, key: str) -> int:
        return len(self.lists[key])

    async def lrange(self, key: str, start: int, stop: int) -> List[bytes]:
        if stop == -1:
            return self.lists[key][start:]
        return self.lists[key][start:stop+1]

    async def set(self, key: str, value: Any, ex: Optional[int] = None):
        self.keys[key] = value

    async def get(self, key: str) -> Optional[Any]:
        return self.keys.get(key)

    async def publish(self, channel: str, message: Any):
        for q in list(self.listeners[channel]):
            await q.put(message)

    def subscribe(self, channel: str) -> asyncio.Queue:
        q: asyncio.Queue[Any] = asyncio.Queue()
        self.listeners[channel].add(q)
        return q

    def unsubscribe(self, channel: str, q: asyncio.Queue):
        self.listeners[channel].discard(q)

    async def acquire_lock(self, lock_name: str, timeout_ms: int = 5000) -> bool:
        if lock_name in self.locks:
            return False
        self.locks.add(lock_name)
        asyncio.create_task(self._auto_release(lock_name, timeout_ms / 1000.0))
        return True

    async def _auto_release(self, lock_name: str, delay: float):
        await asyncio.sleep(delay)
        self.locks.discard(lock_name)

    async def release_lock(self, lock_name: str):
        self.locks.discard(lock_name)


class RedisClientManager:
    """Async Redis Client wrapper with automatic fallback."""
    def __init__(self):
        self.redis = None
        self.use_fallback = False
        self.fallback = InMemoryRedisFallback()

    async def connect(self):
        try:
            import redis.asyncio as aioredis
            self.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=False)
            await self.redis.ping()
            logger.info("Connected to Redis server.")
        except Exception as e:
            logger.warning(f"Redis connection failed ({e}). Using in-memory fallback broker.")
            self.use_fallback = True

    async def close(self):
        if self.redis:
            try:
                await self.redis.close()
            except Exception:
                pass
            finally:
                self.redis = None
        self.use_fallback = False
        self.fallback = InMemoryRedisFallback()

    def _ensure_active(self):
        if self.redis is None:
            self.use_fallback = True

    async def hset(self, key: str, field: str, value: str):
        self._ensure_active()
        if self.use_fallback:
            return await self.fallback.hset(key, field, value)
        await self.redis.hset(key, field, value)

    async def hgetall(self, key: str) -> Dict[bytes, bytes]:
        self._ensure_active()
        if self.use_fallback:
            res = await self.fallback.hgetall(key)
            return {k.encode(): v.encode() for k, v in res.items()}
        return await self.redis.hgetall(key)

    async def hdel(self, key: str, field: str):
        self._ensure_active()
        if self.use_fallback:
            return await self.fallback.hdel(key, field)
        await self.redis.hdel(key, field)

    async def hlen(self, key: str) -> int:
        self._ensure_active()
        if self.use_fallback:
            return await self.fallback.hlen(key)
        return await self.redis.hlen(key)

    async def lpush(self, key: str, value: bytes):
        self._ensure_active()
        if self.use_fallback:
            return await self.fallback.lpush(key, value)
        await self.redis.lpush(key, value)

    async def llen(self, key: str) -> int:
        self._ensure_active()
        if self.use_fallback:
            return await self.fallback.llen(key)
        return await self.redis.llen(key)

    async def lrange(self, key: str, start: int, stop: int) -> List[bytes]:
        self._ensure_active()
        if self.use_fallback:
            return await self.fallback.lrange(key, start, stop)
        return await self.redis.lrange(key, start, stop)

    async def set(self, key: str, value: Any, ex: Optional[int] = None):
        self._ensure_active()
        if self.use_fallback:
            return await self.fallback.set(key, value, ex)
        await self.redis.set(key, value, ex=ex)

    async def get(self, key: str) -> Optional[Any]:
        self._ensure_active()
        if self.use_fallback:
            return await self.fallback.get(key)
        return await self.redis.get(key)

    async def publish(self, channel: str, message: bytes):
        self._ensure_active()
        if self.use_fallback:
            return await self.fallback.publish(channel, message)
        await self.redis.publish(channel, message)

    async def acquire_lock(self, lock_name: str, timeout_ms: int = 5000) -> bool:
        self._ensure_active()
        if self.use_fallback:
            return await self.fallback.acquire_lock(lock_name, timeout_ms)
        val = "1"
        res = await self.redis.set(f"lock:{lock_name}", val, px=timeout_ms, nx=True)
        return bool(res)

    async def release_lock(self, lock_name: str):
        self._ensure_active()
        if self.use_fallback:
            return await self.fallback.release_lock(lock_name)
        await self.redis.delete(f"lock:{lock_name}")

redis_client = RedisClientManager()
