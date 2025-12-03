import jwt
from fastapi import Request, HTTPException
from .config import SECRET_KEY, ALGORITHM

def get_user_from_token(request: Request):
    auth = request.headers.get("Authorization")
    if not auth:
        return None

    if not auth.startswith("Bearer "):
        return None

    token = auth.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload   # Contains user_id, is_admin, email
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")