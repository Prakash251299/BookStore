from sqlalchemy.orm import Session
from . import models
from .auth_utils import hash_password
from datetime import datetime

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user(db: Session, user_id):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, *, email: str, username: str, password: str, full_name: str = None):
    hashed = hash_password(password)
    user = models.User(email=email, username=username, hashed_password=hashed, full_name=full_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_refresh_token(db: Session, user_id, token: str, expires_at: datetime):
    rt = models.RefreshToken(user_id=user_id, token=token, expires_at=expires_at)
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return rt

def get_refresh_token(db: Session, token: str):
    return db.query(models.RefreshToken).filter(models.RefreshToken.token == token).first()

def delete_refresh_token(db: Session, token: str):
    rt = db.query(models.RefreshToken).filter(models.RefreshToken.token == token).first()
    if rt:
        db.delete(rt)
        db.commit()
    return