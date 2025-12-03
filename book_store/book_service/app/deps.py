from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import httpx
from .config import AUTH_SERVICE_URL

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="dummy-login")  # just for docs


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

    return resp.json()  # {id, email, username, is_admin, ...}


def require_admin(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    return current_user