from __future__ import annotations

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DBT_DRAFTS_DIR = BASE_DIR / "dbt_drafts"

SEGMENTS = ["Music", "Sports", "Arts_Theatre", "Family"]
GENRES = [
    "Rock",
    "Pop",
    "Electronic",
    "Urban",
    "Football",
    "Basketball",
    "Tennis",
    "Theatre",
    "Musical",
    "Comedy",
    "Classical",
    "Kids",
    "Circus",
    "Exhibition",
]


def slugify(value: str) -> str:
    return value.lower().replace("&", "and").replace(" ", "_")


def window_model_sql(window_days: int) -> str:
    suffix = f"{window_days}d"
    segment_lines = [
        "    coalesce(safe_divide("
        f"countif(liked and segmento = '{segment}'),"
        f" countif(segmento = '{segment}')"
        f"), 0.0) as like_rate_segment_{slugify(segment)}_{suffix}"
        for segment in SEGMENTS
    ]
    genre_lines = [
        "    coalesce(safe_divide("
        f"countif(liked and genero = '{genre}'),"
        f" countif(genero = '{genre}')"
        f"), 0.0) as like_rate_genre_{slugify(genre)}_{suffix}"
        for genre in GENRES
    ]
    dynamic_fields = ",\n".join(segment_lines + genre_lines)

    return f"""{{{{ config(materialized='table') }}}}

-- Draft generado para clustering.
-- Bloqueos conocidos:
-- 1. `dwell_ms` no esta todavia en stg_swipes/fct_swipes.
-- 2. `precio_min` y `precio_max` llegan como null en fct_swipes.
-- 3. Falta una ciudad de referencia del usuario para features locales.

with base as (
    select *
    from {{{{ ref('fct_swipes') }}}}
    where event_timestamp >= timestamp_sub(current_timestamp(), interval {window_days} day)
),

agg as (
    select
        user_id,
        count(*) as total_swipes_{suffix},
        countif(liked) as total_right_swipes_{suffix},
        coalesce(safe_divide(countif(liked), count(*)), 0.0) as right_swipe_rate_{suffix},
        cast(null as float64) as avg_dwell_ms_{suffix},
        cast(null as float64) as avg_right_dwell_ms_{suffix},
        count(distinct if(liked, segmento, null)) as distinct_segments_liked_{suffix},
        count(distinct if(liked, genero, null)) as distinct_genres_liked_{suffix},
        count(distinct if(liked, ciudad, null)) as distinct_cities_liked_{suffix},
        cast(null as float64) as local_like_rate_{suffix},
        cast(null as float64) as local_swipe_share_{suffix},
        avg(if(liked and fecha_evento is not null, date_diff(fecha_evento, date(event_timestamp), day), null)) as avg_days_until_event_liked_{suffix},
        cast(null as float64) as avg_price_mid_liked_{suffix},
        cast(null as float64) as median_price_mid_liked_{suffix},
        cast(null as float64) as avg_price_mid_disliked_{suffix},
        coalesce(safe_divide(countif(recommendation_context = 'chat'), count(*)), 0.0) as chat_swipe_share_{suffix},
        coalesce(
            safe_divide(
                countif(recommendation_context = 'chat' and liked),
                countif(recommendation_context = 'chat')
            ),
            0.0
        ) as chat_right_rate_{suffix},
        coalesce(
            timestamp_diff(current_timestamp(), max(if(liked, event_timestamp, null)), day),
            {window_days + 7}
        ) as days_since_last_right_swipe_{suffix},
{dynamic_fields}
    from base
    group by user_id
)

select *
from agg
"""


def dim_current_sql() -> str:
    passthrough_columns = [
        "total_swipes_30d",
        "total_right_swipes_30d",
        "right_swipe_rate_30d",
        "avg_dwell_ms_30d",
        "avg_right_dwell_ms_30d",
        "distinct_segments_liked_30d",
        "distinct_genres_liked_30d",
        "distinct_cities_liked_30d",
        "local_like_rate_30d",
        "local_swipe_share_30d",
        "avg_days_until_event_liked_30d",
        "avg_price_mid_liked_30d",
        "median_price_mid_liked_30d",
        "avg_price_mid_disliked_30d",
        "chat_swipe_share_30d",
        "chat_right_rate_30d",
        "days_since_last_right_swipe_30d",
        "total_swipes_90d",
        "total_right_swipes_90d",
        "right_swipe_rate_90d",
        "avg_dwell_ms_90d",
        "avg_right_dwell_ms_90d",
        "distinct_segments_liked_90d",
        "distinct_genres_liked_90d",
        "distinct_cities_liked_90d",
        "local_like_rate_90d",
        "local_swipe_share_90d",
        "avg_days_until_event_liked_90d",
        "avg_price_mid_liked_90d",
        "median_price_mid_liked_90d",
        "avg_price_mid_disliked_90d",
        "chat_swipe_share_90d",
        "chat_right_rate_90d",
        "days_since_last_right_swipe_90d",
    ]
    passthrough_columns.extend([f"like_rate_segment_{slugify(segment)}_90d" for segment in SEGMENTS])
    passthrough_columns.extend([f"like_rate_genre_{slugify(genre)}_90d" for genre in GENRES])

    select_lines = [f"    f30.{column}," for column in passthrough_columns if column.endswith("_30d")]
    select_lines.extend([f"    f90.{column}," for column in passthrough_columns if column.endswith("_90d")])

    return """{{ config(materialized='table') }}

with f30 as (
    select * from {{ ref('int_user_swipe_features_30d') }}
),
f90 as (
    select * from {{ ref('int_user_swipe_features_90d') }}
)

select
    f90.user_id,
""" + "\n".join(select_lines) + """
    coalesce(f30.right_swipe_rate_30d, 0.0) - coalesce(f90.right_swipe_rate_90d, 0.0) as right_swipe_rate_delta_30_vs_90,
    coalesce(f30.total_swipes_30d, 0.0) - coalesce(f90.total_swipes_90d, 0.0) as total_swipes_delta_30_vs_90
from f90
left join f30 using (user_id)
"""


def schema_yml() -> str:
    return """version: 2

models:
  - name: int_user_swipe_features_30d
    description: "Borrador de features de clustering agregadas a 30 dias sobre fct_swipes."
    columns:
      - name: user_id
        description: "Usuario agregado."
        data_tests:
          - not_null
          - unique

  - name: int_user_swipe_features_90d
    description: "Borrador de features de clustering agregadas a 90 dias sobre fct_swipes."
    columns:
      - name: user_id
        description: "Usuario agregado."
        data_tests:
          - not_null
          - unique

  - name: dim_user_cluster_features_current
    description: "Borrador de vista/tabla base para alimentar el entrenamiento del clustering."
    columns:
      - name: user_id
        description: "Usuario listo para clustering."
        data_tests:
          - not_null
          - unique
"""


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    write_file(DBT_DRAFTS_DIR / "int_user_swipe_features_30d.sql", window_model_sql(30))
    write_file(DBT_DRAFTS_DIR / "int_user_swipe_features_90d.sql", window_model_sql(90))
    write_file(DBT_DRAFTS_DIR / "dim_user_cluster_features_current.sql", dim_current_sql())
    write_file(DBT_DRAFTS_DIR / "schema.yml", schema_yml())
    print("Step 2 completed: dbt drafts generated.")
    print(f"Draft directory: {DBT_DRAFTS_DIR}")


if __name__ == "__main__":
    main()
