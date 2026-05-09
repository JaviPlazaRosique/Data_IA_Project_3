import asyncio
import logging

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.auth.dependencies import get_admin_user
from app.config import settings
from app.db.bigquery import bq_table, get_bq_client
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


class SwipeTotals(BaseModel):
    left: int
    right: int


class DailySwipe(BaseModel):
    date: str
    left: int
    right: int


class EventSwipeStats(BaseModel):
    event_id: str
    left: int
    right: int
    total: int
    right_ratio: float


class AnalyticsResponse(BaseModel):
    swipe_totals: SwipeTotals
    daily_swipes: list[DailySwipe]


def _build_date_filter(start_date: str | None, end_date: str | None) -> str:
    if start_date and end_date:
        return f"WHERE DATE(timestamp) BETWEEN '{start_date}' AND '{end_date}'"
    if start_date:
        return f"WHERE DATE(timestamp) >= '{start_date}'"
    if end_date:
        return f"WHERE DATE(timestamp) <= '{end_date}'"
    return ""


def _query_analytics_sync(start_date: str | None, end_date: str | None) -> AnalyticsResponse:
    try:
        table = bq_table(settings.BIGQUERY_MARTS_DATASET, "fct_swipes")
        client = get_bq_client()
        date_filter = _build_date_filter(start_date, end_date)

        totals_rows = list(client.query(f"""
            SELECT
                COUNTIF(direction = 'left') AS left_count,
                COUNTIF(direction = 'right') AS right_count
            FROM {table}
            {date_filter}
        """).result())

        totals = SwipeTotals(left=0, right=0)
        if totals_rows:
            r = totals_rows[0]
            totals = SwipeTotals(left=r["left_count"] or 0, right=r["right_count"] or 0)

        daily_filter = date_filter or "WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)"
        daily = [
            DailySwipe(date=r["date"], left=r["left_count"] or 0, right=r["right_count"] or 0)
            for r in client.query(f"""
                SELECT
                    CAST(DATE(timestamp) AS STRING) AS date,
                    COUNTIF(direction = 'left') AS left_count,
                    COUNTIF(direction = 'right') AS right_count
                FROM {table}
                {daily_filter}
                GROUP BY date
                ORDER BY date ASC
            """).result()
        ]

        return AnalyticsResponse(swipe_totals=totals, daily_swipes=daily)

    except Exception:
        logger.exception("Failed to query analytics from BigQuery")
        return AnalyticsResponse(swipe_totals=SwipeTotals(left=0, right=0), daily_swipes=[])


def _query_event_swipes_sync(limit: int) -> list[EventSwipeStats]:
    try:
        table = bq_table(settings.BIGQUERY_MARTS_DATASET, "fct_swipes")
        rows = list(get_bq_client().query(f"""
            SELECT
                event_id,
                COUNTIF(direction = 'left') AS left_count,
                COUNTIF(direction = 'right') AS right_count,
                COUNT(*) AS total
            FROM {table}
            WHERE event_id IS NOT NULL
            GROUP BY event_id
            ORDER BY total DESC
            LIMIT {limit}
        """).result())

        result = []
        for r in rows:
            total = r["total"] or 0
            right = r["right_count"] or 0
            result.append(EventSwipeStats(
                event_id=r["event_id"],
                left=r["left_count"] or 0,
                right=right,
                total=total,
                right_ratio=round((right / total * 100) if total > 0 else 0.0, 1),
            ))
        return result
    except Exception:
        logger.exception("Failed to query event swipes from BigQuery")
        return []


@router.get("", response_model=AnalyticsResponse)
async def get_analytics(
    _: User = Depends(get_admin_user),
    start_date: str | None = Query(None, description="ISO date YYYY-MM-DD"),
    end_date: str | None = Query(None, description="ISO date YYYY-MM-DD"),
) -> AnalyticsResponse:
    return await asyncio.to_thread(_query_analytics_sync, start_date, end_date)


@router.get("/events", response_model=list[EventSwipeStats])
async def get_event_swipe_stats(
    _: User = Depends(get_admin_user),
    limit: int = Query(20, ge=1, le=100),
) -> list[EventSwipeStats]:
    return await asyncio.to_thread(_query_event_swipes_sync, limit)
