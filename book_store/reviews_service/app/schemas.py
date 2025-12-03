from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict


class ReviewCreate(BaseModel):
    book_id: str
    rating: int
    title: Optional[str] = None
    comment: Optional[str] = None


class ReviewOut(BaseModel):
    id: str
    book_id: str
    user_id: str
    username: str
    rating: int
    title: Optional[str]
    comment: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewDetail(ReviewOut):
    updated_at: Optional[datetime]
    book_title: Optional[str]


class ReviewUpdate(BaseModel):
    rating: Optional[int]
    title: Optional[str]
    comment: Optional[str]


class ReviewListItem(BaseModel):
    id: str
    user_id: str
    username: str
    rating: int
    title: Optional[str]
    comment: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedReviews(BaseModel):
    items: List[ReviewListItem]
    total: int
    page: int
    limit: int
    pages: int
    average_rating: float


class ReviewSummary(BaseModel):
    book_id: str
    total_reviews: int
    average_rating: float
    rating_distribution: Dict[str, int]