import os
from dotenv import load_dotenv

load_dotenv()

# SQLite DB for books service
DATABASE_URL = os.getenv("BOOKS_DATABASE_URL", "sqlite:////var/data/test.db")

# Auth service URL (used for /me admin check)
# AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth_service:8001")

# Redis / fakeredis toggle
USE_FAKEREDIS = False
# REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6380/0")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Internal secret for stock updates from Orders service
INTERNAL_SERVICE_SECRET = os.getenv("INTERNAL_SERVICE_SECRET", "super-secret-internal")