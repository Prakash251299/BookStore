from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time

from .routes import router
from .rate_limiter import rate_limit
from .auth_middleware import get_user_from_token

app = FastAPI(title="API Gateway")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)
    print(f"{request.method} {request.url.path} ➜ {response.status_code} ({duration}ms)")
    return response

# Rate Limiting Middleware
@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    user = get_user_from_token(request)

    if user:
        key = f"user:{user['user_id']}"
        limit = 500 if user.get("is_admin") else 100
    else:
        ip = request.client.host
        key = f"ip:{ip}"
        limit = 20

    rate_limit(key, limit)

    return await call_next(request)

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "services": {
            "auth": "healthy",
            "books": "healthy",
            "orders": "healthy",
            "reviews": "healthy",
        }
    }

app.include_router(router)