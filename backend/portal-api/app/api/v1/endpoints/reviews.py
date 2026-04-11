from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.event_review import EventReview
from app.models.user import User
from app.schemas.event_review import EventReviewCreate, EventReviewRead, EventReviewUpdate

router = APIRouter(tags=["reviews"])


@router.post(
    "/events/{event_id}/reviews",
    response_model=EventReviewRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    event_id: str,
    body: EventReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EventReview:
    review = EventReview(user_id=current_user.id, event_id=event_id, **body.model_dump())
    db.add(review)
    try:
        await db.commit()
        await db.refresh(review)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reviewed this event",
        )
    return review


@router.get("/events/{event_id}/reviews", response_model=list[EventReviewRead])
async def list_event_reviews(
    event_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[EventReview]:
    result = await db.execute(
        select(EventReview)
        .where(EventReview.event_id == event_id)
        .order_by(EventReview.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/users/me/reviews", response_model=list[EventReviewRead])
async def list_my_reviews(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[EventReview]:
    result = await db.execute(
        select(EventReview)
        .where(EventReview.user_id == current_user.id)
        .order_by(EventReview.created_at.desc())
    )
    return list(result.scalars().all())


@router.put("/users/me/reviews/{review_id}", response_model=EventReviewRead)
async def update_my_review(
    review_id: str,
    body: EventReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EventReview:
    result = await db.execute(
        select(EventReview).where(
            EventReview.id == review_id,
            EventReview.user_id == current_user.id,
        )
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
        )
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(review, field, value)
    await db.commit()
    await db.refresh(review)
    return review
