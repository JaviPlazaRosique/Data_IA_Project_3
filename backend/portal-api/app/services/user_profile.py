from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from functools import lru_cache

from google.auth.exceptions import DefaultCredentialsError
from google.cloud import bigquery

from app.config import settings

SAFE_BQ_IDENTIFIER = re.compile(r"^[A-Za-z0-9_-]+$")

_SEGMENTS = ["music", "sports", "arts_theatre", "family"]
_GENRES = [
    "rock", "pop", "electronic", "urban", "football", "basketball",
    "tennis", "theatre", "musical", "comedy", "classical", "kids",
    "circus", "exhibition",
]
_PRICE_BANDS = ["low", "medium", "high"]


@dataclass
class UserTasteProfile:
    top_segments: list[tuple[str, float]]   # [(name, rate), ...]
    top_genres: list[tuple[str, float]]
    dominant_price_band: str | None
    engagement_level: str                   # "baja" | "media" | "alta"
    engagement_trend: str                   # "creciente" | "estable" | "decreciente"

    def to_context_string(self) -> str:
        lines = ["[Perfil de gustos del usuario]"]
        if self.top_segments:
            seg_str = ", ".join(f"{n.replace('_', ' ').title()} ({int(r*100)}%)" for n, r in self.top_segments)
            lines.append(f"Segmentos preferidos: {seg_str}")
        if self.top_genres:
            gen_str = ", ".join(f"{n.replace('_', ' ').title()} ({int(r*100)}%)" for n, r in self.top_genres)
            lines.append(f"Géneros preferidos: {gen_str}")
        if self.dominant_price_band:
            band_label = {"low": "económico", "medium": "medio", "high": "premium"}.get(
                self.dominant_price_band, self.dominant_price_band
            )
            lines.append(f"Precio preferido: {band_label}")
        lines.append(f"Actividad: {self.engagement_level} (tendencia {self.engagement_trend})")
        return "\n".join(lines)


@lru_cache(maxsize=1)
def _get_bigquery_client() -> bigquery.Client:
    project_id = settings.BIGQUERY_PROJECT_ID or settings.GOOGLE_CLOUD_PROJECT or None
    return bigquery.Client(project=project_id)


def _safe_identifier(value: str, label: str) -> str:
    if not SAFE_BQ_IDENTIFIER.fullmatch(value):
        raise RuntimeError(f"Invalid BigQuery {label}: {value!r}")
    return value


def _features_table() -> str:
    project_id = settings.BIGQUERY_PROJECT_ID or settings.GOOGLE_CLOUD_PROJECT
    if not project_id:
        raise RuntimeError("BIGQUERY_PROJECT_ID or GOOGLE_CLOUD_PROJECT must be set")
    project_id = _safe_identifier(project_id, "project id")
    dataset = _safe_identifier(settings.BIGQUERY_MARTS_DATASET, "dataset")
    table = _safe_identifier(settings.BIGQUERY_CLUSTER_FEATURES_TABLE, "table")
    return f"`{project_id}.{dataset}.{table}`"


def _select_columns() -> list[str]:
    cols = ["user_id", "right_swipe_rate_90d", "right_swipe_rate_delta_30_vs_90"]
    for seg in _SEGMENTS:
        cols.append(f"like_rate_segment_{seg}_90d")
    for genre in _GENRES:
        cols.append(f"like_rate_genre_{genre}_90d")
    for band in _PRICE_BANDS:
        cols.append(f"like_rate_price_band_{band}_90d")
    return cols


def _build_profile(row: dict) -> UserTasteProfile:
    # Top 2 segments
    seg_scores = [(seg, float(row.get(f"like_rate_segment_{seg}_90d") or 0)) for seg in _SEGMENTS]
    top_segments = sorted(seg_scores, key=lambda x: x[1], reverse=True)[:2]
    top_segments = [(n, r) for n, r in top_segments if r > 0]

    # Top 3 genres
    genre_scores = [(g, float(row.get(f"like_rate_genre_{g}_90d") or 0)) for g in _GENRES]
    top_genres = sorted(genre_scores, key=lambda x: x[1], reverse=True)[:3]
    top_genres = [(n, r) for n, r in top_genres if r > 0]

    # Dominant price band
    band_scores = {b: float(row.get(f"like_rate_price_band_{b}_90d") or 0) for b in _PRICE_BANDS}
    dominant_price_band = max(band_scores, key=band_scores.get) if any(band_scores.values()) else None

    # Engagement level
    rate = float(row.get("right_swipe_rate_90d") or 0)
    if rate >= 0.5:
        engagement_level = "alta"
    elif rate >= 0.25:
        engagement_level = "media"
    else:
        engagement_level = "baja"

    # Engagement trend
    delta = float(row.get("right_swipe_rate_delta_30_vs_90") or 0)
    if delta > 0.05:
        engagement_trend = "creciente"
    elif delta < -0.05:
        engagement_trend = "decreciente"
    else:
        engagement_trend = "estable"

    return UserTasteProfile(
        top_segments=top_segments,
        top_genres=top_genres,
        dominant_price_band=dominant_price_band,
        engagement_level=engagement_level,
        engagement_trend=engagement_trend,
    )


def _fetch_sync(user_id: str) -> UserTasteProfile | None:
    cols = ", ".join(_select_columns())
    query = f"select {cols} from {_features_table()} where user_id = @user_id limit 1"
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("user_id", "STRING", user_id)]
    )
    rows = list(_get_bigquery_client().query(query, job_config=job_config).result())
    if not rows:
        return None
    return _build_profile(dict(rows[0].items()))


async def fetch_user_taste_profile(user_id: str) -> UserTasteProfile | None:
    try:
        return await asyncio.to_thread(_fetch_sync, user_id)
    except (DefaultCredentialsError, Exception):
        return None
