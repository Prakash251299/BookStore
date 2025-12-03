import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("ORDERS_DATABASE_URL", "sqlite:///./orders.db")

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
BOOKS_SERVICE_URL = os.getenv("BOOKS_SERVICE_URL", "http://localhost:8002")

USE_FAKEREDIS = os.getenv("USE_FAKEREDIS", "False").lower() == "False"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# must match the one used in Books Service for /stock endpoint
INTERNAL_SERVICE_SECRET = os.getenv("INTERNAL_SERVICE_SECRET", "super-secret-internal")