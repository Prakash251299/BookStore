from sqlalchemy import Column, String, Integer, Text, Date, DateTime, Numeric
from sqlalchemy.sql import func
from uuid import uuid4
from .database import Base


def uuid_str():
    return str(uuid4())


class Book(Base):
    __tablename__ = "books"

    id = Column(String(36), primary_key=True, default=uuid_str)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    isbn = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    stock_quantity = Column(Integer, default=0)
    category = Column(String(100))
    publisher = Column(String(255))
    published_date = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Category(Base):
    __tablename__ = "categories"

    id = Column(String(36), primary_key=True, default=uuid_str)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)