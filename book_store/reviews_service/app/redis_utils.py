import json
from .config import USE_FAKEREDIS, REDIS_URL

if USE_FAKEREDIS:
    import fakeredis
    redis_client = fakeredis.FakeStrictRedis(decode_responses=True)
    print("[Reviews] Using fakeredis")
else:
    import redis
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    print("[Reviews] Using real Redis:", REDIS_URL)


def cache_set(key, value, ttl):
    try:
        redis_client.set(key, json.dumps(value), ex=ttl)
    except:
        pass

def cache_get(key):
    try:
        val = redis_client.get(key)
        return json.loads(val) if val else None
    except:
        return None

def cache_delete(key):
    try:
        redis_client.delete(key)
    except:
        pass

def publish_event(topic: str, payload: dict):
    print(f"[PUB] {topic} => {payload}")