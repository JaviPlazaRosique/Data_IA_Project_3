import asyncio
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_admin_user, get_db
from app.config import settings
from app.db.bigquery import bq_table, get_bq_client
from app.db.firestore import get_firestore
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stats", tags=["stats"])


class StatsResponse(BaseModel):
    total_users: int
    active_users: int
    total_events: int
    total_saved_events: int
    total_swipes: int
    new_users_this_week: int
    new_users_last_week: int
    swipes_this_week: int
    swipes_last_week: int


def _count_swipes_with_deltas_sync() -> tuple[int, int, int]:
    try:
        table = bq_table(settings.BIGQUERY_MARTS_DATASET, "fct_swipes")
        rows = list(get_bq_client().query(f"""
            SELECT
                COUNT(*) AS total,
                COUNTIF(DATE(swiped_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)) AS this_week,
                COUNTIF(
                    DATE(swiped_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY)
                    AND DATE(swiped_at) < DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
                ) AS last_week
            FROM {table}
        """).result())
        if rows:
            r = rows[0]
            return r["total"] or 0, r["this_week"] or 0, r["last_week"] or 0
        return 0, 0, 0
    except Exception:
        return -1, -1, -1


async def _count_events() -> int:
    try:
        db = get_firestore()
        docs = await db.collection("eventos").count().get()
        return docs[0][0].value
    except Exception:
        return -1


@router.get("", response_model=StatsResponse)
async def get_stats(
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> StatsResponse:
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    active_users = (
        await db.execute(
            select(func.count()).select_from(User).where(User.is_active == True)  # noqa: E712
        )
    ).scalar_one()
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)
    new_users_this_week = (
        await db.execute(
            select(func.count()).select_from(User).where(User.created_at >= week_ago)
        )
    ).scalar_one()
    new_users_last_week = (
        await db.execute(
            select(func.count()).select_from(User).where(
                User.created_at >= two_weeks_ago,
                User.created_at < week_ago,
            )
        )
    ).scalar_one()
    total_saved_events = (await db.execute(text("SELECT COUNT(*) FROM saved_events"))).scalar_one()

    total_events, (total_swipes, swipes_this_week, swipes_last_week) = await asyncio.gather(
        _count_events(),
        asyncio.to_thread(_count_swipes_with_deltas_sync),
    )

    return StatsResponse(
        total_users=total_users,
        active_users=active_users,
        total_events=total_events,
        total_saved_events=total_saved_events,
        total_swipes=total_swipes,
        new_users_this_week=new_users_this_week,
        new_users_last_week=new_users_last_week,
        swipes_this_week=swipes_this_week,
        swipes_last_week=swipes_last_week,
    )
