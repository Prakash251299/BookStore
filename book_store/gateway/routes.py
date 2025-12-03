from fastapi import APIRouter, Request, HTTPException
import httpx
from config import AUTH_SERVICE, BOOK_SERVICE, ORDER_SERVICE, REVIEW_SERVICE
router = APIRouter()
SERVICE_MAP = {
    "/api/v1/auth": AUTH_SERVICE,
    "/api/v1/books": BOOK_SERVICE,
    "/api/v1/orders": ORDER_SERVICE,
    "/api/v1/reviews": REVIEW_SERVICE,
}

async def forward(request: Request, service_url: str):
    async with httpx.AsyncClient() as client:
        url = service_url + request.url.path
        response = await client.request(
            request.method,
            url,
            headers=request.headers.raw,
            content=await request.body()
        )
    return response

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def gateway_router(request: Request):
    path = request.url.path

    for prefix, service in SERVICE_MAP.items():
        if path.startswith(prefix):
            return await forward(request, service)
    raise HTTPException(status_code=404, detail="Route not found")