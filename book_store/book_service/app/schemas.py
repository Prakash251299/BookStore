from pydantic import BaseModel, condecimal
from typing import Optional, List
from datetime import date, datetime


class BookBase(BaseModel):
    title: str
    author: str
    isbn: str
    description: Optional[str] = None
    price: condecimal(max_digits=10, decimal_places=2)
    stock_quantity: Optional[int] = 0
    category: Optional[str] = None
    publisher: Optional[str] = None
    published_date: Optional[date] = None


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    price: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    stock_quantity: Optional[int] = None
    description: Optional[str] = None
    category: Optional[str] = None
    publisher: Optional[str] = None
    published_date: Optional[date] = None


class BookListItem(BaseModel):
    id: str
    title: str
    author: str
    isbn: str
    price: condecimal(max_digits=10, decimal_places=2)
    stock_quantity: int
    category: Optional[str]

    model_config={"from_attributes":True}

    # class Config:
    #     orm_mode = True


class BookDetail(BookBase):
    id: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    # These can be filled later from Reviews service; for now optional
    average_rating: Optional[float] = None
    review_count: Optional[int] = None

    model_config={"from_attributes":True}

    # class Config:
    #     orm_mode = True


class PaginatedBooks(BaseModel):
    items: list[BookListItem]
    total: int
    page: int
    limit: int
    pages: int


class CategoryOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    book_count: int

    model_config={"from_attributes":True}

    # class Config:
    #     orm_mode = True


class CategoriesResponse(BaseModel):
    categories: List[CategoryOut]


class StockUpdateRequest(BaseModel):
    quantity_change: int


class StockUpdateResponse(BaseModel):
    id: str
    stock_quantity: int
    updated_at: Optional[datetime]