from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session
from math import ceil

from .database import get_db
from . import crud, models, schemas
from .deps import get_current_user, require_admin
from .redis_utils import (
    cache_get,
    cache_set,
    cache_delete,
    make_filters_hash,
    publish_event,
)
from .config import INTERNAL_SERVICE_SECRET

router = APIRouter(prefix="/api/v1/books", tags=["books"])


@router.post("", response_model=schemas.BookDetail, status_code=201)
def create_book(
    payload: schemas.BookCreate,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    try:
        book = crud.create_book(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # clear listing caches & publish event
    publish_event("book.created", {"book_id": book.id})
    return book


@router.get("", response_model=schemas.PaginatedBooks)
def list_books(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category: str | None = None,
    author: str | None = None,
    search: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    sort_by: str | None = Query(None, regex="^(price|title|published_date)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    filters = {
        "page": page,
        "limit": limit,
        "category": category,
        "author": author,
        "search": search,
        "min_price": min_price,
        "max_price": max_price,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }
    filters_hash = make_filters_hash(filters)
    cache_key = f"books:list:{page}:{filters_hash}"

    cached = cache_get(cache_key)
    if cached:
        return cached

    items, total = crud.list_books(
        db,
        page=page,
        limit=limit,
        category=category,
        author=author,
        search=search,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    pages = ceil(total / limit) if limit else 1

    resp = schemas.PaginatedBooks(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )
    cache_set(cache_key, resp.dict(), ttl=15 * 60)
    return resp



@router.get("/categories", response_model=schemas.CategoriesResponse)
def get_categories(db: Session = Depends(get_db)):
    cache_key = "categories:all"
    print("called")
    cached = cache_get(cache_key)
    if cached:
        return cached
    rows = crud.get_categories_with_counts(db)
    categories = [
        schemas.CategoryOut(
            id=row.id,
            name=row.name,
            description=row.description,
            book_count=row.book_count or 0,
        )
        for row in rows
    ]
    resp = schemas.CategoriesResponse(categories=categories)
    cache_set(cache_key, resp.dict(), ttl=24 * 60 * 60)
    return resp


@router.get("/{book_id}", response_model=schemas.BookDetail)
def get_book(
    book_id: str,
    db: Session = Depends(get_db),
):
    cache_key = f"book:{book_id}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # TODO: later enrich with average_rating & review_count from Reviews service
    detail = schemas.BookDetail.from_orm(book)
    cache_set(cache_key, detail.dict(), ttl=60 * 60)
    return detail


@router.put("/{book_id}", response_model=schemas.BookDetail)
def update_book(
    book_id: str,
    payload: schemas.BookUpdate,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    book = crud.update_book(db, book, payload)
    # invalidate caches
    cache_delete(f"book:{book_id}")
    # in real life, also clear list caches; here we skip or rely on TTL
    publish_event("book.updated", {"book_id": book.id})
    return schemas.BookDetail.from_orm(book)


@router.delete("/{book_id}", status_code=204)
def delete_book(
    book_id: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    crud.delete_book(db, book)
    cache_delete(f"book:{book_id}")
    return


@router.patch("/{book_id}/stock", response_model=schemas.StockUpdateResponse)
def update_stock(
    book_id: str,
    payload: schemas.StockUpdateRequest,
    db: Session = Depends(get_db),
    x_internal_secret: str = Header(default=None, alias="X-Internal-Secret"),
):
    if x_internal_secret != INTERNAL_SERVICE_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    try:
        book = crud.update_stock(db, book, payload.quantity_change)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    cache_delete(f"book:{book_id}")
    if (book.stock_quantity or 0) < 10:
        publish_event("book.stock_low", {"book_id": book.id, "stock_quantity": book.stock_quantity})

    return schemas.StockUpdateResponse(
        id=book.id,
        stock_quantity=book.stock_quantity,
        updated_at=book.updated_at,
    )