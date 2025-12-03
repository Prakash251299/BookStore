import os
from dotenv import load_dotenv
load_dotenv()

AUTH_SERVICE = os.getenv("AUTH_SERVICE", "http://auth_service:8001")
BOOK_SERVICE = os.getenv("BOOK_SERVICE", "http://book_service:8002")
ORDER_SERVICE = os.getenv("ORDER_SERVICE", "http://orders_service:8003")
REVIEW_SERVICE = os.getenv("REVIEW_SERVICE", "http://reviews_service:8004")

USE_FAKEREDIS = os.getenv("USE_FAKEREDIS", "true").lower() == "true"
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
ALGORITHM = "HS256"