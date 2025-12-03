from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from typing import Optional, List, Tuple
from math import ceil

from . import models
from .schemas import BookCreate, BookUpdate


def create_book(db: Session, data: BookCreate) -> models.Book:
    # Check ISBN unique
    existing = db.query(models.Book).filter(models.Book.isbn == data.isbn).first()
    if existing:
        raise ValueError("ISBN already exists")

    book = models.Book(**data.dict())
    db.add(book)

    # ensure category exists in categories table
    if data.category:
        cat = db.query(models.Category).filter(models.Category.name == data.category).first()
        if not cat:
            cat = models.Category(name=data.category, description=None)
            db.add(cat)

    db.commit()
    db.refresh(book)
    return book


def get_book(db: Session, book_id: str) -> Optional[models.Book]:
    return db.query(models.Book).filter(models.Book.id == book_id).first()


def update_book(db: Session, book: models.Book, data: BookUpdate) -> models.Book:
    for field, value in data.dict(exclude_unset=True).items():
        setattr(book, field, value)

    # update category table if category changed
    if "category" in data.dict(exclude_unset=True) and book.category:
        cat = db.query(models.Category).filter(models.Category.name == book.category).first()
        if not cat:
            cat = models.Category(name=book.category, description=None)
            db.add(cat)

    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def delete_book(db: Session, book: models.Book) -> None:
    db.delete(book)
    db.commit()


def list_books(
    db: Session,
    page: int = 1,
    limit: int = 20,
    category: Optional[str] = None,
    author: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
) -> Tuple[List[models.Book], int]:
    query = db.query(models.Book)

    if category:
        query = query.filter(models.Book.category == category)
    if author:
        query = query.filter(models.Book.author == author)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(models.Book.title.ilike(like), models.Book.description.ilike(like)))
    if min_price is not None:
        query = query.filter(models.Book.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Book.price <= max_price)

    # total before pagination
    total = query.count()

    # sorting
    sort_column = {
        "price": models.Book.price,
        "title": models.Book.title,
        "published_date": models.Book.published_date,
    }.get(sort_by or "", models.Book.created_at)

    if sort_order == "desc":
        sort_column = sort_column.desc()
    query = query.order_by(sort_column)

    # pagination
    items = query.offset((page - 1) * limit).limit(limit).all()
    return items, total


def get_categories_with_counts(db: Session):
    # left join books to categories by name
    # simpler: aggregate directly from books and join category desc
    sub = (
        db.query(models.Book.category, func.count(models.Book.id).label("book_count"))
        .group_by(models.Book.category)
        .subquery()
    )

    q = (
        db.query(
            models.Category.id,
            models.Category.name,
            models.Category.description,
            func.coalesce(sub.c.book_count, 0).label("book_count"),
        )
        .outerjoin(sub, models.Category.name == sub.c.category)
    )

    return q.all()


def update_stock(db: Session, book: models.Book, quantity_change: int) -> models.Book:
    new_qty = (book.stock_quantity or 0) + quantity_change
    if new_qty < 0:
        raise ValueError("Insufficient stock")
    book.stock_quantity = new_qty
    db.add(book)
    db.commit()
    db.refresh(book)
    return book