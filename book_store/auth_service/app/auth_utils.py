from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_SECONDS, REFRESH_TOKEN_EXPIRE_SECONDS

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(subject: str, user_id: str, expires_delta: Optional[int]=None):
    expire = datetime.utcnow() + timedelta(seconds=(expires_delta or ACCESS_TOKEN_EXPIRE_SECONDS))
    payload = {"sub": subject, "user_id": user_id, "exp": expire}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, int((expire - datetime.utcnow()).total_seconds())

def create_refresh_token(subject: str, user_id: str, expires_delta: Optional[int]=None):
    expire = datetime.utcnow() + timedelta(seconds=(expires_delta or REFRESH_TOKEN_EXPIRE_SECONDS))
    payload = {"sub": subject, "user_id": user_id, "exp": expire}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, expire