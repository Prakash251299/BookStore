from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from math import ceil
from decimal import Decimal

from .database import get_db
from . import schemas, crud, models
from .deps import get_current_user, require_admin, fetch_book, update_book_stock
from .redis_utils import cache_get, cache_set, cache_delete, publish_event

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])


# --------- Helpers --------- #

def build_order_detail(
    db: Session,
    order: models.Order,
    books_cache: dict[str, dict] | None = None,
) -> schemas.OrderDetail:
    items = crud.get_order_items(db, order.id)
    result_items = []

    if books_cache is None:
        books_cache = {}

    for it in items:
        if it.book_id not in books_cache:
            books_cache[it.book_id] = fetch_book(it.book_id)

        book_data = books_cache[it.book_id]
        result_items.append(
            schemas.OrderItemOut(
                id=it.id,
                book_id=it.book_id,
                book_title=book_data.get("title"),
                quantity=it.quantity,
                price_at_purchase=Decimal(str(it.price_at_purchase)),
                subtotal=Decimal(str(it.subtotal)),
            )
        )

    return schemas.OrderDetail(
        id=order.id,
        user_id=order.user_id,
        status=order.status,
        items=result_items,
        total_amount=Decimal(str(order.total_amount)),
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


# --------- Endpoints --------- #

@router.post("", response_model=schemas.OrderDetail, status_code=201)
def create_order(
    payload: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not payload.items:
        raise HTTPException(status_code=400, detail="No items in order")

    # Fetch books and validate stock
    books_cache: dict[str, dict] = {}
    items_data_for_db = []

    for item in payload.items:
        b = fetch_book(item.book_id)
        books_cache[item.book_id] = b

        stock = b.get("stock_quantity", 0)
        if stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for book {b.get('title')}")

        price = Decimal(str(b["price"]))
        subtotal = price * item.quantity

        items_data_for_db.append(
            {
                "book_id": item.book_id,
                "quantity": item.quantity,
                "price_at_purchase": price,
                "subtotal": subtotal,
            }
        )

    # Deduct stock in Books service
    for item in payload.items:
        update_book_stock(item.book_id, -item.quantity)

    order = crud.create_order(db, current_user["id"], items_data_for_db)

    # clear caches
    cache_delete(f"orders:user:{current_user['id']}:page:1:all")  # simple invalidation
    cache_delete(f"order:{order.id}")

    publish_event("order.created", {"order_id": order.id, "user_id": order.user_id})
    return build_order_detail(db, order, books_cache)


@router.get("", response_model=schemas.PaginatedOrders)
def list_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, regex="^(pending|processing|completed|cancelled)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    cache_key = f"orders:user:{current_user['id']}:page:{page}:{status or 'all'}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    orders, total = crud.list_orders_for_user(db, current_user["id"], page, limit, status)
    items = []
    for o in orders:
        item_count = len(crud.get_order_items(db, o.id))
        items.append(
            schemas.OrderListItem(
                id=o.id,
                status=o.status,
                total_amount=Decimal(str(o.total_amount)),
                item_count=item_count,
                created_at=o.created_at,
                updated_at=o.updated_at,
            )
        )

    pages = ceil(total / limit) if limit else 1
    resp = schemas.PaginatedOrders(items=items, total=total, page=page, limit=limit, pages=pages)
    cache_set(cache_key, resp.dict(), ttl=5 * 60)
    return resp



@router.get("/stats", response_model=schemas.OrderStats)
def get_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    total_orders, total_spent, orders_by_status, total_books = crud.get_user_stats(db, current_user["id"])
    return schemas.OrderStats(
        total_orders=total_orders,
        total_spent=Decimal(str(total_spent)),
        orders_by_status=orders_by_status,
        total_books_purchased=total_books,
    )


@router.get("/{order_id}", response_model=schemas.OrderDetail)
def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    cache_key = f"order:{order_id}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != current_user["id"] and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Forbidden")

    detail = build_order_detail(db, order)
    cache_set(cache_key, detail.dict(), ttl=10 * 60)
    return detail


@router.patch("/{order_id}/status", response_model=schemas.OrderStatusUpdateResponse)
def update_order_status(
    order_id: str,
    payload: schemas.OrderStatusUpdateRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    allowed = {"pending", "processing", "completed", "cancelled"}
    if payload.status not in allowed:
        raise HTTPException(status_code=400, detail="Invalid status")

    # simple transition rule: can't go from cancelled/completed back
    if order.status in {"cancelled", "completed"} and payload.status != order.status:
        raise HTTPException(status_code=400, detail="Invalid status transition")

    order = crud.update_order_status(db, order, payload.status)
    cache_delete(f"order:{order_id}")

    if payload.status == "completed":
        publish_event("order.completed", {"order_id": order.id, "user_id": order.user_id})
    elif payload.status == "cancelled":
        publish_event("order.cancelled", {"order_id": order.id, "user_id": order.user_id})

    return schemas.OrderStatusUpdateResponse(id=order.id, status=order.status, updated_at=order.updated_at)


@router.delete("/{order_id}", response_model=schemas.OrderCancelResponse)
def cancel_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != current_user["id"] and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Forbidden")

    if order.status != "pending":
        raise HTTPException(status_code=400, detail="Cannot cancel order in current status")

    order = crud.cancel_order(db, order)
    cache_delete(f"order:{order_id}")

    publish_event("order.cancelled", {"order_id": order.id, "user_id": order.user_id})

    return schemas.OrderCancelResponse(
        id=order.id,
        status=order.status,
        message="Order cancelled successfully",
    )