import json
from .config import USE_FAKEREDIS, REDIS_URL

if USE_FAKEREDIS:
    import fakeredis

    redis_client = fakeredis.FakeStrictRedis(decode_responses=True)
    print("[OrdersService] Using fakeredis (in-memory)")
else:
    import redis

    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    print("[OrdersService] Using real Redis:", REDIS_URL)


def cache_set(key: str, value: dict, ttl: int):
    try:
        redis_client.set(key, json.dumps(value), ex=ttl)
    except Exception as e:
        print("[Redis] cache_set error:", e)


def cache_get(key: str):
    try:
        data = redis_client.get(key)
        return json.loads(data) if data else None
    except Exception as e:
        print("[Redis] cache_get error:", e)
        return None


def cache_delete(key: str):
    try:
        redis_client.delete(key)
    except Exception as e:
        print("[Redis] cache_delete error:", e)


def publish_event(topic: str, payload: dict):
    # placeholder for real pub/sub
    print(f"[PUB] topic={topic} payload={payload}")