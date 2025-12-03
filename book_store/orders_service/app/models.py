from sqlalchemy import Column, String, DateTime, Numeric, Integer, ForeignKey
from sqlalchemy.sql import func
from uuid import uuid4
from .database import Base


def uuid_str():
    return str(uuid4())


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=uuid_str)
    user_id = Column(String(36), nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending, processing, completed, cancelled
    total_amount = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(String(36), primary_key=True, default=uuid_str)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(String(36), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_at_purchase = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)