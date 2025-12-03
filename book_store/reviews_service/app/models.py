from sqlalchemy import Column, String, Integer, Text, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from uuid import uuid4
from .database import Base

def uuid_str():
    return str(uuid4())

class Review(Base):
    __tablename__ = "reviews"

    id = Column(String(36), primary_key=True, default=uuid_str)
    book_id = Column(String(36), nullable=False)
    user_id = Column(String(36), nullable=False)
    username = Column(String(100), nullable=False)
    rating = Column(Integer, nullable=False)    # 1-5
    title = Column(String(255))
    comment = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("book_id", "user_id", name="uq_book_user"),
    )