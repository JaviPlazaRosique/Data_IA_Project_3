from __future__ import annotations

import asyncio
import csv
import re
from functools import lru_cache
from pathlib import Path

from google.api_core.exceptions import NotFound
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import bigquery

from app.config import settings
from app.models.user import User
from app.schemas.recommendation import ClusterRecommendationRead

SAFE_BQ_IDENTIFIER = re.compile(r"^[A-Za-z0-9_-]+$")


@lru_cache(maxsize=1)
def _get_bigquery_client() -> bigquery.Client:
    project_id = settings.BIGQUERY_PROJECT_ID or settings.GOOGLE_CLOUD_PROJECT or None
    return bigquery.Client(project=project_id)


def _safe_identifier(value: str, label: str) -> str:
    if not SAFE_BQ_IDENTIFIER.fullmatch(value):
        raise RuntimeError(f"Invalid BigQuery {label}: {value!r}")
    return value


def _recommendations_table() -> str:
    project_id = settings.BIGQUERY_PROJECT_ID or settings.GOOGLE_CLOUD_PROJECT
    if not project_id:
        raise RuntimeError("BIGQUERY_PROJECT_ID or GOOGLE_CLOUD_PROJECT must be set to read recommendations from BigQuery")
    project_id = _safe_identifier(project_id, "project id")
    dataset = _safe_identifier(settings.BIGQUERY_MARTS_DATASET, "dataset")
    table = _safe_identifier(settings.BIGQUERY_RECOMMENDATIONS_TABLE, "table")
    return (
        f"`{project_id}."
        f"{dataset}."
        f"{table}`"
    )


def _marts_table(table_name: str) -> str:
    project_id = settings.BIGQUERY_PROJECT_ID or settings.GOOGLE_CLOUD_PROJECT
    if not project_id:
        raise RuntimeError("BIGQUERY_PROJECT_ID or GOOGLE_CLOUD_PROJECT must be set to read marts from BigQuery")
    project_id = _safe_identifier(project_id, "project id")
    dataset = _safe_identifier(settings.BIGQUERY_MARTS_DATASET, "dataset")
    table_name = _safe_identifier(table_name, "table")
    return f"`{project_id}.{dataset}.{table_name}`"


def _events_table() -> str:
    project_id = settings.BIGQUERY_PROJECT_ID or settings.GOOGLE_CLOUD_PROJECT
    if not project_id:
        raise RuntimeError("BIGQUERY_PROJECT_ID or GOOGLE_CLOUD_PROJECT must be set to read events from BigQuery")
    project_id = _safe_identifier(project_id, "project id")
    dataset = _safe_identifier(settings.BIGQUERY_ANALYTICS_DATASET, "dataset")
    return f"`{project_id}.{dataset}.eventos`"


def _query_recommendations_sync(user_id: str, limit: int) -> list[ClusterRecommendationRead]:
    query = f"""
select
  event_id,
  event_name,
  cast(fecha_evento as string) as fecha_evento,
  ciudad,
  recinto_nombre,
  segmento,
  genero,
  subgenero,
  recommendation_rank,
  recommendation_score,
  cluster_source
from {_recommendations_table()}
where user_id = @user_id
order by recommendation_rank asc
limit @limit
""".strip()
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
        ],
    )
    rows = _get_bigquery_client().query(query, job_config=job_config).result()
    return [ClusterRecommendationRead(**dict(row.items())) for row in rows]


def _query_cold_start_recommendations_sync(user: User, limit: int) -> list[ClusterRecommendationRead]:
    preferred_categories = user.preferred_categories or []
    query = f"""
with event_catalog as (
  select
    id as event_id,
    coalesce(nullif(cast(e.uuid_evento as string), ''), cast(id as string)) as uuid_evento,
    nombre as event_name,
    cast(fecha as string) as fecha_evento,
    fecha,
    ciudad,
    recinto_nombre,
    segmento,
    genero,
    subgenero,
    (
      if(@preferred_location is not null and lower(ciudad) = lower(@preferred_location), 0.8, 0.0)
      + if(
          array_length(@preferred_categories) > 0
          and exists (
            select 1
            from unnest(@preferred_categories) category
            where lower(concat(
              coalesce(segmento, ''), ' ',
              coalesce(genero, ''), ' ',
              coalesce(subgenero, ''), ' ',
              coalesce(categoria, ''), ' ',
              coalesce(subcategoria, '')
            )) like concat('%', lower(category), '%')
          ),
          1.0,
          0.0
        )
      + greatest(0.0, 0.20 - date_diff(fecha, current_date(), day) * 0.003)
    ) as recommendation_score
  from {_events_table()} e
  left join (
    select distinct
      coalesce(nullif(cast(e.uuid_evento as string), ''), cast(s.event_id as string)) as uuid_evento
    from {_marts_table("fct_swipes")} s
    left join {_events_table()} e
      on e.id = s.event_id
    where s.user_id = @user_id
  ) seen
    on seen.uuid_evento = coalesce(nullif(cast(e.uuid_evento as string), ''), cast(e.id as string))
  where id is not null
    and fecha is not null
    and fecha >= current_date()
    and seen.uuid_evento is null
),

scored_events as (
  select * except(fecha)
  from event_catalog
  qualify row_number() over (
    partition by uuid_evento
    order by recommendation_score desc, fecha asc, event_id asc
  ) = 1
)
select
  event_id,
  event_name,
  fecha_evento,
  ciudad,
  recinto_nombre,
  segmento,
  genero,
  subgenero,
  row_number() over (
    order by recommendation_score desc, fecha_evento asc, event_id asc
  ) as recommendation_rank,
  recommendation_score,
  'cold_start' as cluster_source
from scored_events
order by recommendation_rank asc
limit @limit
""".strip()
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("preferred_location", "STRING", user.preferred_location),
            bigquery.ArrayQueryParameter("preferred_categories", "STRING", preferred_categories),
            bigquery.ScalarQueryParameter("user_id", "STRING", str(user.id)),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
        ],
    )
    rows = _get_bigquery_client().query(query, job_config=job_config).result()
    return [ClusterRecommendationRead(**dict(row.items())) for row in rows]


def _query_local_fallback(user_id: str, limit: int) -> list[ClusterRecommendationRead]:
    if not settings.DEV_RECOMMENDATIONS_FALLBACK_PATH:
        return []

    path = Path(settings.DEV_RECOMMENDATIONS_FALLBACK_PATH)
    if not path.exists():
        return []

    recommendations: list[ClusterRecommendationRead] = []
    with path.open(newline="", encoding="utf-8") as csv_file:
        for row in csv.DictReader(csv_file):
            if row.get("user_id") != user_id:
                continue
            recommendations.append(
                ClusterRecommendationRead(
                    event_id=row["event_id"],
                    event_name=row.get("event_name") or None,
                    fecha_evento=row.get("fecha_evento") or None,
                    ciudad=row.get("ciudad") or None,
                    recinto_nombre=row.get("recinto_nombre") or None,
                    segmento=row.get("segmento") or None,
                    genero=row.get("genero") or None,
                    subgenero=row.get("subgenero") or None,
                    recommendation_rank=int(row["recommendation_rank"]),
                    recommendation_score=float(row["recommendation_score"]),
                    cluster_source=row["cluster_source"],
                )
            )

    return sorted(recommendations, key=lambda rec: rec.recommendation_rank)[:limit]


async def list_user_recommendations(user: User, limit: int) -> list[ClusterRecommendationRead]:
    user_id = str(user.id)
    try:
        try:
            recommendations = await asyncio.to_thread(_query_recommendations_sync, user_id, limit)
        except NotFound:
            recommendations = []
        if recommendations:
            return recommendations
        return await asyncio.to_thread(_query_cold_start_recommendations_sync, user, limit)
    except DefaultCredentialsError:
        fallback = await asyncio.to_thread(_query_local_fallback, user_id, limit)
        if fallback:
            return fallback
        raise
