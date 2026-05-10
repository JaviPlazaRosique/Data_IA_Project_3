import asyncio
import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.dependencies import get_admin_user
from app.config import settings
from app.db.bigquery import bq_table, get_bq_client
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kpis", tags=["kpis"])


class EngagementKPIs(BaseModel):
    active_users_7d: int
    active_users_30d: int
    total_swipes_30d: int
    right_swipes_30d: int
    avg_right_swipe_rate: float
    avg_dwell_ms: float
    avg_dwell_liked_ms: float
    avg_plans_per_active_user: float


class SegmentStat(BaseModel):
    name: str
    total: int
    liked: int
    like_rate: float


class CityActivity(BaseModel):
    city: str
    total_swipes: int
    liked: int
    like_rate: float


class DailyActivity(BaseModel):
    date: str
    swipes: int
    likes: int


class PlannerUsage(BaseModel):
    total_chat_swipes_30d: int
    chat_right_rate: float


class KPIsResponse(BaseModel):
    engagement: EngagementKPIs
    top_segments: list[SegmentStat]
    top_genres: list[SegmentStat]
    top_cities: list[CityActivity]
    daily_activity_30d: list[DailyActivity]
    planner: PlannerUsage


def _query_kpis_sync() -> KPIsResponse:
    client = get_bq_client()
    fct = bq_table(settings.BIGQUERY_MARTS_DATASET, "fct_swipes")

    engagement_rows = list(client.query(f"""
        SELECT
            COUNT(DISTINCT IF(event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY), user_id, NULL)) AS active_users_7d,
            COUNT(DISTINCT IF(event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY), user_id, NULL)) AS active_users_30d,
            COUNTIF(event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)) AS total_swipes_30d,
            COUNTIF(event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY) AND liked) AS right_swipes_30d,
            ROUND(COALESCE(SAFE_DIVIDE(COUNTIF(event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY) AND liked),
                COUNTIF(event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY))), 0.0) * 100, 1) AS avg_right_swipe_rate,
            ROUND(COALESCE(AVG(IF(event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY), CAST(dwell_ms AS FLOAT64), NULL)), 0.0), 0) AS avg_dwell_ms,
            ROUND(COALESCE(AVG(IF(event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY) AND liked, CAST(dwell_ms AS FLOAT64), NULL)), 0.0), 0) AS avg_dwell_liked_ms,
            ROUND(COALESCE(SAFE_DIVIDE(
                COUNTIF(event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)),
                COUNT(DISTINCT IF(event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY), user_id, NULL))
            ), 0.0), 1) AS avg_plans_per_active_user
        FROM {fct}
        WHERE ingestion_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 31 DAY)
    """).result())

    eng = EngagementKPIs(
        active_users_7d=0, active_users_30d=0,
        total_swipes_30d=0, right_swipes_30d=0,
        avg_right_swipe_rate=0.0, avg_dwell_ms=0.0, avg_dwell_liked_ms=0.0,
        avg_plans_per_active_user=0.0,
    )
    if engagement_rows:
        r = engagement_rows[0]
        eng = EngagementKPIs(
            active_users_7d=r["active_users_7d"] or 0,
            active_users_30d=r["active_users_30d"] or 0,
            total_swipes_30d=r["total_swipes_30d"] or 0,
            right_swipes_30d=r["right_swipes_30d"] or 0,
            avg_right_swipe_rate=float(r["avg_right_swipe_rate"] or 0),
            avg_dwell_ms=float(r["avg_dwell_ms"] or 0),
            avg_dwell_liked_ms=float(r["avg_dwell_liked_ms"] or 0),
            avg_plans_per_active_user=float(r["avg_plans_per_active_user"] or 0),
        )

    segment_rows = list(client.query(f"""
        SELECT
            segmento AS name,
            COUNT(*) AS total,
            COUNTIF(liked) AS liked,
            ROUND(SAFE_DIVIDE(COUNTIF(liked), COUNT(*)) * 100, 1) AS like_rate
        FROM {fct}
        WHERE segmento IS NOT NULL
          AND ingestion_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 31 DAY)
        GROUP BY segmento
        ORDER BY total DESC
        LIMIT 10
    """).result())
    top_segments = [
        SegmentStat(name=r["name"], total=r["total"] or 0, liked=r["liked"] or 0, like_rate=float(r["like_rate"] or 0))
        for r in segment_rows
    ]

    genre_rows = list(client.query(f"""
        SELECT
            genero AS name,
            COUNT(*) AS total,
            COUNTIF(liked) AS liked,
            ROUND(SAFE_DIVIDE(COUNTIF(liked), COUNT(*)) * 100, 1) AS like_rate
        FROM {fct}
        WHERE genero IS NOT NULL
          AND ingestion_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 31 DAY)
        GROUP BY genero
        ORDER BY total DESC
        LIMIT 10
    """).result())
    top_genres = [
        SegmentStat(name=r["name"], total=r["total"] or 0, liked=r["liked"] or 0, like_rate=float(r["like_rate"] or 0))
        for r in genre_rows
    ]

    city_rows = list(client.query(f"""
        SELECT
            ciudad AS city,
            COUNT(*) AS total_swipes,
            COUNTIF(liked) AS liked,
            ROUND(SAFE_DIVIDE(COUNTIF(liked), COUNT(*)) * 100, 1) AS like_rate
        FROM {fct}
        WHERE ciudad IS NOT NULL
          AND ingestion_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 31 DAY)
        GROUP BY ciudad
        ORDER BY total_swipes DESC
        LIMIT 10
    """).result())
    top_cities = [
        CityActivity(city=r["city"], total_swipes=r["total_swipes"] or 0, liked=r["liked"] or 0, like_rate=float(r["like_rate"] or 0))
        for r in city_rows
    ]

    daily_rows = list(client.query(f"""
        SELECT
            CAST(DATE(event_timestamp) AS STRING) AS date,
            COUNT(*) AS swipes,
            COUNTIF(liked) AS likes
        FROM {fct}
        WHERE event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
          AND ingestion_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 31 DAY)
        GROUP BY date
        ORDER BY date ASC
    """).result())
    daily_activity = [
        DailyActivity(date=r["date"], swipes=r["swipes"] or 0, likes=r["likes"] or 0)
        for r in daily_rows
    ]

    planner_rows = list(client.query(f"""
        SELECT
            COUNTIF(recommendation_context = 'chat'
                    AND event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)) AS chat_swipes,
            ROUND(SAFE_DIVIDE(
                COUNTIF(recommendation_context = 'chat' AND liked
                        AND event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)),
                COUNTIF(recommendation_context = 'chat'
                        AND event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY))
            ) * 100, 1) AS chat_right_rate
        FROM {fct}
        WHERE ingestion_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 31 DAY)
    """).result())
    planner = PlannerUsage(total_chat_swipes_30d=0, chat_right_rate=0.0)
    if planner_rows:
        r = planner_rows[0]
        planner = PlannerUsage(
            total_chat_swipes_30d=r["chat_swipes"] or 0,
            chat_right_rate=float(r["chat_right_rate"] or 0),
        )

    return KPIsResponse(
        engagement=eng,
        top_segments=top_segments,
        top_genres=top_genres,
        top_cities=top_cities,
        daily_activity_30d=daily_activity,
        planner=planner,
    )


@router.get("", response_model=KPIsResponse)
async def get_kpis(
    _: User = Depends(get_admin_user),
) -> KPIsResponse:
    try:
        return await asyncio.to_thread(_query_kpis_sync)
    except Exception:
        logger.exception("Failed to query KPIs from BigQuery")
        return KPIsResponse(
            engagement=EngagementKPIs(
                active_users_7d=-1, active_users_30d=-1,
                total_swipes_30d=-1, right_swipes_30d=-1,
                avg_right_swipe_rate=-1, avg_dwell_ms=-1, avg_dwell_liked_ms=-1,
                avg_plans_per_active_user=-1,
            ),
            top_segments=[], top_genres=[], top_cities=[],
            daily_activity_30d=[], planner=PlannerUsage(total_chat_swipes_30d=-1, chat_right_rate=-1),
        )
