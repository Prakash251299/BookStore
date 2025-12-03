from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import httpx

from .config import AUTH_SERVICE_URL, BOOKS_SERVICE_URL

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="dummy")


def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        resp = httpx.get(f"{AUTH_SERVICE_URL}/api/v1/auth/me",
                         headers={"Authorization": f"Bearer {token}"})
    except:
        raise HTTPException(status_code=503, detail="Auth service unavailable")

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json().get("detail"))

    return resp.json()  # {id, username, is_admin, ...}


def fetch_book(book_id: str):
    try:
        resp = httpx.get(f"{BOOKS_SERVICE_URL}/api/v1/books/{book_id}")
    except:
        raise HTTPException(status_code=503, detail="Books service unavailable")

    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Book not found")

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())

    return resp.json()