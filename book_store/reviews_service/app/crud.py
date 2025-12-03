from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict
from . import models


def create_review(db: Session, data: dict):
    review = models.Review(**data)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def get_review(db: Session, review_id: str):
    return db.query(models.Review).filter(models.Review.id == review_id).first()


def get_user_review_for_book(db: Session, user_id: str, book_id: str):
    return db.query(models.Review).filter(
        models.Review.user_id == user_id,
        models.Review.book_id == book_id
    ).first()


def list_reviews_for_book(db: Session, book_id: str, page: int, limit: int,
                          rating: Optional[int], sort_by: str, order: str):
    q = db.query(models.Review).filter(models.Review.book_id == book_id)

    if rating:
        q = q.filter(models.Review.rating == rating)

    if order == "asc":
        if sort_by == "rating":
            q = q.order_by(models.Review.rating.asc())
        else:
            q = q.order_by(models.Review.created_at.asc())
    else:
        if sort_by == "rating":
            q = q.order_by(models.Review.rating.desc())
        else:
            q = q.order_by(models.Review.created_at.desc())

    total = q.count()
    items = q.offset((page-1)*limit).limit(limit).all()
    return items, total


def get_reviews_by_user(db: Session, user_id: str, page: int, limit: int):
    q = db.query(models.Review).filter(models.Review.user_id == user_id)
    total = q.count()
    items = q.order_by(models.Review.created_at.desc()).offset((page-1)*limit).limit(limit).all()
    return items, total


def update_review(db: Session, review: models.Review, data: dict):
    for k, v in data.items():
        setattr(review, k, v)
    db.commit()
    db.refresh(review)
    return review


def delete_review(db: Session, review: models.Review):
    db.delete(review)
    db.commit()


def review_summary(db: Session, book_id: str):
    rows = db.query(
        models.Review.rating, func.count(models.Review.id)
    ).filter(
        models.Review.book_id == book_id
    ).group_by(models.Review.rating).all()

    total = sum(count for _, count in rows) or 0
    avg = sum(rating * count for rating, count in rows) / total if total else 0

    dist = {str(i): 0 for i in range(1, 6)}
    for rating, count in rows:
        dist[str(rating)] = count

    return total, avg, dist