import redis
import json
from datetime import datetime, timedelta


USE_FAKEREDIS = False

if USE_FAKEREDIS:
    import fakeredis
    # Use FakeRedis for in-memory operations
    redis_client = fakeredis.FakeRedis(decode_responses=True)
else:
    # Use the real Redis client if USE_FAKEREDIS is False
    from .config import REDIS_URL
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)


def cache_user_profile(user_id: str, profile: dict, ttl_seconds: int = 3600):
    """Caches a user profile using SET with an expiration time."""
    key = f"user:{user_id}"
    redis_client.set(key, json.dumps(profile), ex=ttl_seconds)

def get_cached_user_profile(user_id: str):
    """Retrieves a cached user profile."""
    key = f"user:{user_id}"
    data = redis_client.get(key)
    return json.loads(data) if data else None

def blacklist_token(token: str, ttl_seconds: int):
    """Stores a blacklisted token with a TTL using SET."""
    key = f"token:blacklist:{token}"
    redis_client.set(key, "1", ex=ttl_seconds)

def is_token_blacklisted(token: str):
    """Checks if a token exists in the blacklist."""
    key = f"token:blacklist:{token}"
    return redis_client.exists(key) == 1


def publish_event(topic: str, payload: dict):
    # for now just print; in production publish to GCP Pub/Sub
    print(f"[PUB] topic={topic} payload={payload}")
    # redis_client.publish(topic, json.dumps(payload))


# import redis
# import json
# from .config import REDIS_URL
# from datetime import datetime, timedelta

# redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# def cache_user_profile(user_id: str, profile: dict, ttl_seconds: int = 3600):
#     pass
#     # key = f"user:{user_id}"
#     # redis_client.set(key, json.dumps(profile), ex=ttl_seconds)

# def get_cached_user_profile(user_id: str):
#     key = f"user:{user_id}"
#     data = redis_client.get(key)
#     return json.loads(data) if data else None

# def blacklist_token(token: str, ttl_seconds: int):
#     # store token in blacklist set with TTL
#     key = f"token:blacklist:{token}"
#     redis_client.set(key, "1", ex=ttl_seconds)

# def is_token_blacklisted(token: str):
#     key = f"token:blacklist:{token}"
#     return redis_client.exists(key) == 1

# # simple pubsub stub (replace with GCP Pub/Sub)
# def publish_event(topic: str, payload: dict):
#     # for now just print; in production publish to GCP Pub/Sub
#     print(f"[PUB] topic={topic} payload={payload}")