import time
from typing import Tuple
from app.core.redis import redis_client

class SlidingWindowRateLimiter:
    """
    True Sliding Window Rate Limiter using Redis Sorted Set (ZADD/ZREMRANGEBYSCORE pipeline).
    Prevents window-boundary burst attacks.
    """
    def __init__(self, requests_limit: int = 60, window_seconds: int = 60):
        self.limit = requests_limit
        self.window = window_seconds

    async def is_allowed(self, identifier: str) -> Tuple[bool, int]:
        now = time.time()
        window_start = now - self.window
        key = f"ratelimit:sw:{identifier}"

        try:
            if not redis_client.use_fallback and redis_client.redis:
                async with redis_client.redis.pipeline() as pipe:
                    pipe.zremrangebyscore(key, 0, window_start)
                    pipe.zcard(key)
                    pipe.zadd(key, {str(now): now})
                    pipe.expire(key, int(self.window * 2))
                    results = await pipe.execute()
                count = results[1]
            else:
                # Fallback in-memory rate limiting
                count_key = f"{key}:count"
                current = await redis_client.get(count_key)
                count = int(current) if current else 0
                await redis_client.set(count_key, count + 1, ex=self.window)
        except Exception:
            return True, self.limit  # Fail open on Redis error

        if count >= self.limit:
            return False, 0
        return True, self.limit - count - 1

rate_limiter = SlidingWindowRateLimiter(requests_limit=60, window_seconds=60)
