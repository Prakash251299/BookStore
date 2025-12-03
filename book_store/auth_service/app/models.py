import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .database import Base
from sqlalchemy import Text
from uuid import uuid4

class User(Base):
    __tablename__ = "users"
    # id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id = Column(String(36), primary_key=True, default=lambda:str(uuid4()))
    email = Column(String(256), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    full_name = Column(String(256))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(String(36), primary_key=True, default=lambda:str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"),nullable=False)
    token = Column(Text, unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())