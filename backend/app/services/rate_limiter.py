import time
from typing import Tuple
from app.core.redis import redis_client

class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter using Redis hash & timestamp keys.
    Limits execution, auth attempts, and WS handshakes per IP/User.
    """
    def __init__(self, requests_limit: int = 30, window_seconds: int = 60):
        self.limit = requests_limit
        self.window = window_seconds

    async def is_allowed(self, identifier: str) -> Tuple[bool, int]:
        now = int(time.time())
        key = f"rate_limit:{identifier}:{now // self.window}"
        current = await redis_client.get(key)
        count = int(current) if current else 0
        if count >= self.limit:
            return False, 0
        await redis_client.set(key, count + 1, ex=self.window * 2)
        return True, self.limit - (count + 1)

rate_limiter = SlidingWindowRateLimiter(requests_limit=60, window_seconds=60)
