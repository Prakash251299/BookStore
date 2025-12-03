import time
import json
from fastapi import HTTPException
from config import USE_FAKEREDIS, REDIS_URL

if USE_FAKEREDIS:
    import fakeredis
    redis_client = fakeredis.FakeRedis()
else:
    import redis
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)

def rate_limit(key: str, limit: int, ttl: int = 60):
    """
    Redis Sliding Window Counter
    """
    current = redis_client.get(key)
    if current is None:
        redis_client.set(key, 1, ex=ttl)
        return
    if int(current) >= limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    redis_client.incr(key)