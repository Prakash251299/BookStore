from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Tuple, Optional
from decimal import Decimal

from . import models


def create_order(
    db: Session,
    user_id: str,
    items_data: List[dict],
) -> models.Order:
    total_amount = sum(Decimal(str(i["subtotal"])) for i in items_data)

    order = models.Order(
        user_id=user_id,
        status="pending",
        total_amount=total_amount,
    )
    db.add(order)
    db.flush()  # get order.id

    for i in items_data:
        item = models.OrderItem(
            order_id=order.id,
            book_id=i["book_id"],
            quantity=i["quantity"],
            price_at_purchase=i["price_at_purchase"],
            subtotal=i["subtotal"],
        )
        db.add(item)

    db.commit()
    db.refresh(order)
    return order


def get_order(db: Session, order_id: str) -> Optional[models.Order]:
    return db.query(models.Order).filter(models.Order.id == order_id).first()


def list_orders_for_user(
    db: Session,
    user_id: str,
    page: int,
    limit: int,
    status: Optional[str] = None,
) -> Tuple[List[models.Order], int]:
    q = db.query(models.Order).filter(models.Order.user_id == user_id)
    if status:
        q = q.filter(models.Order.status == status)

    total = q.count()
    items = (
        q.order_by(models.Order.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return items, total


def get_order_items(db: Session, order_id: str) -> List[models.OrderItem]:
    return db.query(models.OrderItem).filter(models.OrderItem.order_id == order_id).all()


def update_order_status(db: Session, order: models.Order, new_status: str) -> models.Order:
    order.status = new_status
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def cancel_order(db: Session, order: models.Order) -> models.Order:
    order.status = "cancelled"
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def get_user_stats(db: Session, user_id: str):
    total_orders = db.query(func.count(models.Order.id)).filter(models.Order.user_id == user_id).scalar() or 0
    total_spent = (
        db.query(func.coalesce(func.sum(models.Order.total_amount), 0))
        .filter(models.Order.user_id == user_id, models.Order.status == "completed")
        .scalar()
        or 0
    )

    orders_by_status_rows = (
        db.query(models.Order.status, func.count(models.Order.id))
        .filter(models.Order.user_id == user_id)
        .group_by(models.Order.status)
        .all()
    )
    orders_by_status = {status: count for status, count in orders_by_status_rows}

    total_books_purchased = (
        db.query(func.coalesce(func.sum(models.OrderItem.quantity), 0))
        .join(models.Order, models.Order.id == models.OrderItem.order_id)
        .filter(models.Order.user_id == user_id, models.Order.status == "completed")
        .scalar()
        or 0
    )

    return total_orders, total_spent, orders_by_status, total_books_purchased