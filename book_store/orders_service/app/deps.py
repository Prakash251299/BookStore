from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
import httpx

from .config import AUTH_SERVICE_URL, BOOKS_SERVICE_URL, INTERNAL_SERVICE_SECRET

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="dummy")


def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = httpx.get(f"{AUTH_SERVICE_URL}/api/v1/auth/me", headers=headers, timeout=5.0)
    except Exception:
        raise HTTPException(status_code=503, detail="Auth service unavailable")

    if resp.status_code == 401:
        raise HTTPException(status_code=401, detail="Invalid token")

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Auth service error")

    return resp.json()  # {id, is_admin, ...}


def require_admin(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    return current_user


def fetch_book(book_id: str):
    try:
        resp = httpx.get(f"{BOOKS_SERVICE_URL}/api/v1/books/{book_id}", timeout=5.0)
    except Exception:
        raise HTTPException(status_code=503, detail="Books service unavailable")

    if resp.status_code == 404:
        raise HTTPException(status_code=400, detail=f"Invalid book_id: {book_id}")

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Books service error")

    return resp.json()


def update_book_stock(book_id: str, quantity_change: int):
    try:
        resp = httpx.patch(
            f"{BOOKS_SERVICE_URL}/api/v1/books/{book_id}/stock",
            json={"quantity_change": quantity_change},
            headers={"X-Internal-Secret": INTERNAL_SERVICE_SECRET},
            timeout=5.0,
        )
    except Exception:
        raise HTTPException(status_code=503, detail="Books service unavailable")

    if resp.status_code == 400:
        raise HTTPException(status_code=400, detail=resp.json().get("detail", "Insufficient stock"))

    if resp.status_code == 404:
        raise HTTPException(status_code=400, detail=f"Invalid book_id: {book_id}")

    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=resp.status_code, detail="Books service stock update error")

    return resp.json()