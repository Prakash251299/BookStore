from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from math import ceil

from .database import get_db
from . import crud, schemas
from .deps import get_current_user, fetch_book
from .redis_utils import cache_get, cache_set, cache_delete, publish_event

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])


# ---------------- CREATE REVIEW ---------------- #

@router.post("", response_model=schemas.ReviewOut, status_code=201)
def create_review(payload: schemas.ReviewCreate,
                  db: Session = Depends(get_db),
                  current_user: dict = Depends(get_current_user)):

    book = fetch_book(payload.book_id)

    existing = crud.get_user_review_for_book(db, current_user["id"], payload.book_id)
    if existing:
        raise HTTPException(status_code=400, detail="You already reviewed this book")

    data = {
        "book_id": payload.book_id,
        "user_id": current_user["id"],
        "username": current_user["username"],
        "rating": payload.rating,
        "title": payload.title,
        "comment": payload.comment,
    }

    review = crud.create_review(db, data)

    # invalidate caches
    cache_delete(f"reviews:book:{payload.book_id}:page:1")
    cache_delete(f"reviews:user:{current_user['id']}:page:1")
    cache_delete(f"reviews:summary:{payload.book_id}")

    publish_event("review.created", {"review_id": review.id})

    return review


# ---------------- LIST REVIEWS FOR BOOK ---------------- #

@router.get("/book/{book_id}", response_model=schemas.PaginatedReviews)
def list_reviews(book_id: str,
                 page: int = Query(1, ge=1),
                 limit: int = Query(20, ge=1, le=100),
                 rating: int | None = Query(None),
                 sort_by: str = Query("created_at"),
                 sort_order: str = Query("desc"),
                 db: Session = Depends(get_db)):

    cache_key = f"reviews:book:{book_id}:page:{page}:{rating}:{sort_by}:{sort_order}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    items, total = crud.list_reviews_for_book(
        db, book_id, page, limit, rating, sort_by, sort_order
    )

    pages = ceil(total / limit) if limit else 1

    # compute average rating
    total_reviews, avg, _ = crud.review_summary(db, book_id)

    resp = schemas.PaginatedReviews(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
        average_rating=round(avg, 1),
    )

    cache_set(cache_key, resp.model_dump(), ttl=10 * 60)
    return resp


# ---------------- GET REVIEW ---------------- #

@router.get("/{review_id}", response_model=schemas.ReviewDetail)
def get_review(review_id: str,
               db: Session = Depends(get_db)):

    review = crud.get_review(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    book = fetch_book(review.book_id)

    return schemas.ReviewDetail(
        id=review.id,
        book_id=review.book_id,
        book_title=book["title"],
        user_id=review.user_id,
        username=review.username,
        rating=review.rating,
        title=review.title,
        comment=review.comment,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


# ---------------- UPDATE REVIEW ---------------- #

@router.put("/{review_id}", response_model=schemas.ReviewOut)
def update_review(review_id: str,
                  payload: schemas.ReviewUpdate,
                  db: Session = Depends(get_db),
                  current_user: dict = Depends(get_current_user)):

    review = crud.get_review(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id != current_user["id"] and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not allowed")

    review = crud.update_review(db, review, payload.model_dump(exclude_unset=True))

    cache_delete(f"reviews:book:{review.book_id}:page:1")
    cache_delete(f"reviews:user:{review.user_id}:page:1")
    cache_delete(f"reviews:summary:{review.book_id}")

    publish_event("review.updated", {"review_id": review.id})

    return review


# ---------------- DELETE REVIEW ---------------- #

@router.delete("/{review_id}", status_code=204)
def delete_review(review_id: str,
                  db: Session = Depends(get_db),
                  current_user: dict = Depends(get_current_user)):

    review = crud.get_review(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id != current_user["id"] and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not allowed")

    crud.delete_review(db, review)

    cache_delete(f"reviews:book:{review.book_id}:page:1")
    cache_delete(f"reviews:user:{review.user_id}:page:1")
    cache_delete(f"reviews:summary:{review.book_id}")

    publish_event("review.deleted", {"review_id": review.id})

    return


# ---------------- USER’S OWN REVIEWS ---------------- #

@router.get("/user/me", response_model=schemas.PaginatedReviews)
def get_my_reviews(page: int = 1, limit: int = 20,
                   db: Session = Depends(get_db),
                   current_user: dict = Depends(get_current_user)):

    cache_key = f"reviews:user:{current_user['id']}:page:{page}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    items, total = crud.get_reviews_by_user(db, current_user["id"], page, limit)
    pages = ceil(total / limit) if limit else 1

    resp = schemas.PaginatedReviews(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
        average_rating=0,
    )

    cache_set(cache_key, resp.model_dump(), ttl=10 * 60)
    return resp


# ---------------- SUMMARY ---------------- #

@router.get("/book/{book_id}/summary", response_model=schemas.ReviewSummary)
def summary(book_id: str,
            db: Session = Depends(get_db)):

    cache_key = f"reviews:summary:{book_id}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    total, avg, dist = crud.review_summary(db, book_id)

    resp = schemas.ReviewSummary(
        book_id=book_id,
        total_reviews=total,
        average_rating=round(avg, 1),
        rating_distribution=dist,
    )

    cache_set(cache_key, resp.model_dump(), ttl=15 * 60)
    return resp