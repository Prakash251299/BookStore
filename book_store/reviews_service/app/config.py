import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("REVIEWS_DATABASE_URL", "sqlite:///./reviews.db")

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth_service:8001")
BOOKS_SERVICE_URL = os.getenv("BOOKS_SERVICE_URL", "http://books_service:8002")

USE_FAKEREDIS = os.getenv("USE_FAKEREDIS", "False").lower() == "False"
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")