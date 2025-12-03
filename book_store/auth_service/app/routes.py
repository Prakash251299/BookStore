from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from . import schemas, crud, auth_utils, redis_utils
from .config import OWNER_SECRET
from .database import get_db
from fastapi import Header
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
import jwt

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

@router.post("/register", response_model=schemas.UserOut, status_code=201)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if crud.get_user_by_username(db, payload.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    user = crud.create_user(db, email=payload.email, username=payload.username, password=payload.password, full_name=payload.full_name)
    # publish event & cache profile
    redis_utils.publish_event("user.registered", {"user_id": str(user.id), "email": user.email})
    redis_utils.cache_user_profile(str(user.id), {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None
    })
    return user

@router.post("/login", response_model=schemas.TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm has username and password fields
    user = crud.get_user_by_username(db, form_data.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not auth_utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account inactive")
    access_token, expires_in = auth_utils.create_access_token(user.username, str(user.id))
    refresh_token, expires_at = auth_utils.create_refresh_token(user.username, str(user.id))
    crud.create_refresh_token(db, user_id=user.id, token=refresh_token, expires_at=expires_at)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer", "expires_in": expires_in}

@router.post("/refresh", response_model=schemas.TokenResponse)
def refresh_token(req: schemas.TokenRefreshRequest, db: Session = Depends(get_db)):
    rt = crud.get_refresh_token(db, req.refresh_token)
    if not rt:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    # verify jwt expiry
    try:
        payload = jwt.decode(req.refresh_token, auth_utils.SECRET_KEY if hasattr(auth_utils, "SECRET_KEY") else None, algorithms=[auth_utils.ALGORITHM] if hasattr(auth_utils, "ALGORITHM") else ["HS256"])
    except Exception:
        # token invalid/expired
        crud.delete_refresh_token(db, req.refresh_token)
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    # create new access token
    access_token, expires_in = auth_utils.create_access_token(subject=payload.get("sub"), user_id=str(rt.user_id))
    return {"access_token": access_token, "refresh_token": None, "token_type": "bearer", "expires_in": expires_in}

def get_current_user_from_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # check blacklist
    if redis_utils.is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token revoked")
    try:
        payload = jwt.decode(token, auth_utils.SECRET_KEY if hasattr(auth_utils, "SECRET_KEY") else None, algorithms=[auth_utils.ALGORITHM] if hasattr(auth_utils, "ALGORITHM") else ["HS256"])
        user_id = payload.get("user_id")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    # Try cache
    cached = redis_utils.get_cached_user_profile(user_id)
    if cached:
        return cached
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    profile = {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }
    redis_utils.cache_user_profile(user_id, profile)
    return profile

@router.get("/me", response_model=schemas.UserOut)
def me(current: dict = Depends(get_current_user_from_token)):
    # current is profile dict
    return current

@router.post("/logout")
def logout(req: schemas.TokenRefreshRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # blacklist access token & remove refresh token
    # find refresh token in DB and delete
    crud.delete_refresh_token(db, req.refresh_token)
    # compute TTL — for simplicity, set to REFRESH_TOKEN_EXPIRE_SECONDS
    from .config import REFRESH_TOKEN_EXPIRE_SECONDS
    redis_utils.blacklist_token(token, REFRESH_TOKEN_EXPIRE_SECONDS)
    return {"message": "Successfully logged out"}

@router.put("/profile", response_model=schemas.UserOut)
def update_profile(payload: schemas.ProfileUpdate, current: dict = Depends(get_current_user_from_token), db: Session = Depends(get_db)):
    user = crud.get_user(db, current["id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.email and payload.email != user.email:
        # ensure uniqueness
        if crud.get_user_by_email(db, payload.email):
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = payload.email
    if payload.full_name is not None:
        user.full_name = payload.full_name
    db.add(user)
    db.commit()
    db.refresh(user)
    profile = {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }
    redis_utils.cache_user_profile(str(user.id), profile)
    redis_utils.publish_event("user.updated", profile)
    return profile


@router.post("/make-admin/{username}")
def make_admin(
    username: str,
    db: Session = Depends(get_db),
    x_owner_secret: str = Header(None, alias="X-Owner-Secret"),
):
    if x_owner_secret != OWNER_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_admin = True
    db.commit()
    return {"message": "User promoted to admin", "username": username}