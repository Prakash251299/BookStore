from pydantic import BaseModel, condecimal
from typing import List, Optional, Dict
from datetime import datetime
from uuid import UUID


class OrderItemCreate(BaseModel):
    book_id: str
    quantity: int


class OrderCreate(BaseModel):
    items: List[OrderItemCreate]


class OrderItemOut(BaseModel):
    id: str
    book_id: str
    book_title: Optional[str] = None
    quantity: int
    price_at_purchase: condecimal(max_digits=10, decimal_places=2)
    subtotal: condecimal(max_digits=10, decimal_places=2)

    model_config = {"from_attributes": True}


class OrderDetail(BaseModel):
    id: str
    user_id: str
    status: str
    items: List[OrderItemOut]
    total_amount: condecimal(max_digits=10, decimal_places=2)
    created_at: Optional[datetime]
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class OrderListItem(BaseModel):
    id: str
    status: str
    total_amount: condecimal(max_digits=10, decimal_places=2)
    item_count: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PaginatedOrders(BaseModel):
    items: List[OrderListItem]
    total: int
    page: int
    limit: int
    pages: int


class OrderStatusUpdateRequest(BaseModel):
    status: str  # pending, processing, completed, cancelled


class OrderStatusUpdateResponse(BaseModel):
    id: str
    status: str
    updated_at: Optional[datetime]


class OrderCancelResponse(BaseModel):
    id: str
    status: str
    message: str


class OrderStats(BaseModel):
    total_orders: int
    total_spent: condecimal(max_digits=10, decimal_places=2)
    orders_by_status: Dict[str, int]
    total_books_purchased: int