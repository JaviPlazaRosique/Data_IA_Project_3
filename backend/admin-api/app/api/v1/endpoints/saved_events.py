from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_admin_user, get_db
from app.models.user import User

router = APIRouter(prefix="/saved-events", tags=["saved-events"])


class TopSavedEvent(BaseModel):
    event_id: str
    event_title: str | None
    event_venue: str | None
    save_count: int


class RecentSave(BaseModel):
    event_id: str
    event_title: str | None
    user_email: str
    saved_at: str


class SavedEventsAdminResponse(BaseModel):
    total: int
    top_events: list[TopSavedEvent]
    recent_saves: list[RecentSave]


@router.get("", response_model=SavedEventsAdminResponse)
async def list_saved_events(
    limit: int = Query(20, ge=1, le=100),
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> SavedEventsAdminResponse:
    total = (await db.execute(text("SELECT COUNT(*) FROM saved_events"))).scalar_one()

    top_rows = (await db.execute(text("""
        SELECT event_id, MAX(event_title) AS event_title, MAX(event_venue) AS event_venue, COUNT(*) AS save_count
        FROM saved_events
        GROUP BY event_id
        ORDER BY save_count DESC
        LIMIT :limit
    """), {"limit": limit})).fetchall()

    top_events = [
        TopSavedEvent(
            event_id=r.event_id,
            event_title=r.event_title,
            event_venue=r.event_venue,
            save_count=r.save_count,
        )
        for r in top_rows
    ]

    recent_rows = (await db.execute(text("""
        SELECT se.event_id, se.event_title, u.email, se.created_at
        FROM saved_events se
        JOIN users u ON se.user_id = u.id
        ORDER BY se.created_at DESC
        LIMIT 20
    """))).fetchall()

    recent_saves = [
        RecentSave(
            event_id=r.event_id,
            event_title=r.event_title,
            user_email=r.email,
            saved_at=r.created_at.isoformat(),
        )
        for r in recent_rows
    ]

    return SavedEventsAdminResponse(total=total, top_events=top_events, recent_saves=recent_saves)
