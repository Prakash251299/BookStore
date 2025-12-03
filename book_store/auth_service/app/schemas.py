from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None

class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    full_name: Optional[str]
    is_active: bool
    is_admin: bool = False
    created_at: Optional[datetime]

    class Config:
        orm_mode = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    expires_in: int

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class ProfileUpdate(BaseModel):
    full_name: Optional[str]
    email: Optional[EmailStr]