from __future__ import annotations

import argparse
import subprocess

from demo_config import DEFAULT_PROJECT_ID


DEFAULT_RAW_DATASET = "recomendacion_planes"
DEFAULT_STAGING_DATASET = "recomendacion_planes_staging"
DEFAULT_INTERMEDIATE_DATASET = "recomendacion_planes_intermediate"
DEFAULT_MARTS_DATASET = "recomendacion_planes_marts"

SEGMENT_RATES = [
    ("music", "Music"),
    ("sports", "Sports"),
    ("arts_theatre", "Arts_Theatre"),
    ("family", "Family"),
]

GENRE_RATES = [
    ("rock", "Rock"),
    ("pop", "Pop"),
    ("electronic", "Electronic"),
    ("urban", "Urban"),
    ("football", "Football"),
    ("basketball", "Basketball"),
    ("tennis", "Tennis"),
    ("theatre", "Theatre"),
    ("musical", "Musical"),
    ("comedy", "Comedy"),
    ("classical", "Classical"),
    ("kids", "Kids"),
    ("circus", "Circus"),
    ("exhibition", "Exhibition"),
]

PRICE_BANDS = [
    ("low", "bajo"),
    ("medium", "medio"),
    ("high", "alto"),
]

PREFERENCE_PREFIXES = [
    "like_rate",
    "swipe_share",
    "liked_share",
    "preference_lift",
]

FEATURE_DEFAULTS = [
    ("total_swipes", "0"),
    ("total_right_swipes", "0"),
    ("right_swipe_rate", "0.0"),
    ("avg_dwell_ms", "0.0"),
    ("avg_right_dwell_ms", "0.0"),
    ("distinct_segments_liked", "0"),
    ("distinct_genres_liked", "0"),
    ("distinct_cities_liked", "0"),
    ("local_like_rate", "0.0"),
    ("local_swipe_share", "0.0"),
    ("avg_days_until_event_liked", "0.0"),
    ("avg_price_mid_liked", "0.0"),
    ("median_price_mid_liked", "0.0"),
    ("avg_price_mid_disliked", "0.0"),
    ("chat_swipe_share", "0.0"),
    ("chat_right_rate", "0.0"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refresh the analytical swipe layer using bq CLI as a local demo fallback."
    )
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--raw-dataset", default=DEFAULT_RAW_DATASET)
    parser.add_argument("--staging-dataset", default=DEFAULT_STAGING_DATASET)
    parser.add_argument("--intermediate-dataset", default=DEFAULT_INTERMEDIATE_DATASET)
    parser.add_argument("--marts-dataset", default=DEFAULT_MARTS_DATASET)
    return parser.parse_args()


def table(project_id: str, dataset: str, name: str) -> str:
    return f"`{project_id}.{dataset}.{name}`"


def run_bq(project_id: str, sql: str, label: str) -> None:
    print(f"Refreshing {label}...")
    command = [
        "bq",
        "query",
        f"--project_id={project_id}",
        "--use_legacy_sql=false",
        "--quiet",
        sql,
    ]
    subprocess.run(command, check=True)


def staging_sql(project_id: str, raw_dataset: str, staging_dataset: str) -> str:
    return f"""
create or replace view {table(project_id, staging_dataset, "stg_swipes")} as
select
    message_id                                            as interaction_id,
    safe_cast(json_value(data, '$.swiped_at') as timestamp) as event_timestamp,
    json_value(data, '$.schema_version')                  as schema_version,
    json_value(data, '$.user_id')                         as user_id,
    json_value(data, '$.session_id')                      as session_id,
    json_value(data, '$.event_id')                        as event_id,
    coalesce(json_value(data, '$.interaction_type'), 'swipe') as interaction_type,
    json_value(data, '$.direction')                       as swipe_direction,
    case json_value(data, '$.direction')
        when 'right' then true
        when 'left'  then false
        else false
    end                                                   as liked,
    safe_cast(json_value(data, '$.dwell_ms') as int64)    as dwell_ms,
    json_value(data, '$.recommendation_context')          as recommendation_context,
    safe_cast(json_value(data, '$.rank_position') as int64) as rank_position,
    json_value(data, '$.recommendation_id')               as recommendation_id,
    json_value(data, '$.producer.surface')                as producer_surface,
    json_value(data, '$.producer.client_version')         as producer_client_version,
    json_value(data, '$.event_snapshot.event_id')         as snapshot_event_id,
    json_value(data, '$.event_snapshot.segmento')         as snapshot_segmento,
    json_value(data, '$.event_snapshot.genero')           as snapshot_genero,
    json_value(data, '$.event_snapshot.subgenero')        as snapshot_subgenero,
    json_value(data, '$.event_snapshot.ciudad')           as snapshot_ciudad,
    json_value(data, '$.event_snapshot.recinto_id')       as snapshot_recinto_id,
    safe_cast(json_value(data, '$.event_snapshot.fecha_evento') as date) as snapshot_fecha_evento,
    safe_cast(json_value(data, '$.event_snapshot.precio_min') as float64) as snapshot_precio_min,
    safe_cast(json_value(data, '$.event_snapshot.precio_max') as float64) as snapshot_precio_max,
    json_value(data, '$.event_snapshot.banda_precio')     as snapshot_banda_precio,
    publish_time                                          as ingestion_timestamp
from {table(project_id, raw_dataset, "swipes_raw")}
where data is not null
  and json_value(data, '$.event_id')   is not null
  and json_value(data, '$.user_id')    is not null
  and json_value(data, '$.direction')  in ('left', 'right')
  and safe_cast(json_value(data, '$.swiped_at') as timestamp) is not null
""".strip()


def fct_sql(project_id: str, raw_dataset: str, staging_dataset: str, marts_dataset: str) -> str:
    return f"""
create or replace table {table(project_id, marts_dataset, "fct_swipes")}
partition by date(ingestion_timestamp)
cluster by user_id as
with swipes as (
    select *
    from {table(project_id, staging_dataset, "stg_swipes")}
    where ingestion_timestamp > timestamp_sub(current_timestamp(), interval 365 day)
),

eventos as (
    select
        id          as event_id,
        segmento,
        genero,
        subgenero,
        ciudad,
        recinto_id,
        fecha       as fecha_evento,
        banda_precio
    from {table(project_id, raw_dataset, "eventos")}
),

dedup as (
    select
        s.*,
        row_number() over (partition by interaction_id order by ingestion_timestamp desc) as rn
    from swipes s
)

select
    d.interaction_id,
    d.event_timestamp,
    d.schema_version,
    d.user_id,
    d.session_id,
    d.event_id,
    d.interaction_type,
    d.swipe_direction,
    d.liked,
    d.dwell_ms,
    d.recommendation_context,
    d.rank_position,
    d.recommendation_id,
    d.producer_surface,
    d.producer_client_version,
    coalesce(d.snapshot_segmento, e.segmento) as segmento,
    coalesce(d.snapshot_genero, e.genero) as genero,
    coalesce(d.snapshot_subgenero, e.subgenero) as subgenero,
    coalesce(d.snapshot_ciudad, e.ciudad) as ciudad,
    case lower(coalesce(d.snapshot_banda_precio, e.banda_precio))
        when 'bajo'  then 0.0
        when 'medio' then 30.0
        when 'alto'  then 60.0
    end as precio_min,
    case lower(coalesce(d.snapshot_banda_precio, e.banda_precio))
        when 'bajo'  then 30.0
        when 'medio' then 60.0
        when 'alto'  then 120.0
    end as precio_max,
    coalesce(d.snapshot_banda_precio, e.banda_precio) as banda_precio,
    case lower(coalesce(d.snapshot_banda_precio, e.banda_precio))
        when 'bajo' then 1
        when 'medio' then 2
        when 'alto' then 3
    end as banda_precio_score,
    case lower(coalesce(d.snapshot_banda_precio, e.banda_precio))
        when 'bajo' then 15.0
        when 'medio' then 45.0
        when 'alto' then 90.0
    end as price_proxy_mid,
    coalesce(d.snapshot_fecha_evento, e.fecha_evento) as fecha_evento,
    coalesce(d.snapshot_recinto_id, e.recinto_id) as recinto_id,
    d.ingestion_timestamp
from dedup d
left join eventos e using (event_id)
where d.rn = 1
""".strip()


def feature_preference_sql(
    source_expression: str,
    alias_prefix: str,
    values: list[tuple[str, str]],
    suffix: str,
) -> str:
    expressions: list[str] = []
    for name, value in values:
        expressions.extend(
            [
                (
                    f"coalesce(safe_divide(countif(liked and {source_expression} = '{value}'), "
                    f"countif({source_expression} = '{value}')), 0.0) "
                    f"as like_rate_{alias_prefix}_{name}_{suffix}"
                ),
                (
                    f"coalesce(safe_divide(countif({source_expression} = '{value}'), count(*)), 0.0) "
                    f"as swipe_share_{alias_prefix}_{name}_{suffix}"
                ),
                (
                    f"coalesce(safe_divide(countif(liked and {source_expression} = '{value}'), countif(liked)), 0.0) "
                    f"as liked_share_{alias_prefix}_{name}_{suffix}"
                ),
                (
                    f"coalesce(safe_divide(countif(liked and {source_expression} = '{value}'), "
                    f"countif({source_expression} = '{value}')), 0.0) "
                    f"- coalesce(safe_divide(countif(liked), count(*)), 0.0) "
                    f"as preference_lift_{alias_prefix}_{name}_{suffix}"
                ),
            ]
        )
    return ",\n        ".join(expressions)


def features_sql(project_id: str, intermediate_dataset: str, marts_dataset: str, window_days: int) -> str:
    suffix = f"{window_days}d"
    default_days_since = 37 if window_days == 30 else 97
    segment_preferences = feature_preference_sql("segmento", "segment", SEGMENT_RATES, suffix)
    genre_preferences = feature_preference_sql("genero", "genre", GENRE_RATES, suffix)
    price_preferences = feature_preference_sql("lower(banda_precio)", "price_band", PRICE_BANDS, suffix)

    return f"""
create or replace table {table(project_id, intermediate_dataset, f"int_user_swipe_features_{suffix}")} as
with base as (
    select
        *,
        coalesce(
            case
                when precio_min is not null and precio_max is not null
                    then (precio_min + precio_max) / 2.0
            end,
            price_proxy_mid
        ) as price_mid
    from {table(project_id, marts_dataset, "fct_swipes")}
    where event_timestamp >= timestamp_sub(current_timestamp(), interval {window_days} day)
),

agg as (
    select
        user_id,
        count(*) as total_swipes_{suffix},
        countif(liked) as total_right_swipes_{suffix},
        coalesce(safe_divide(countif(liked), count(*)), 0.0) as right_swipe_rate_{suffix},
        coalesce(avg(cast(dwell_ms as float64)), 0.0) as avg_dwell_ms_{suffix},
        coalesce(avg(if(liked, cast(dwell_ms as float64), null)), 0.0) as avg_right_dwell_ms_{suffix},
        count(distinct if(liked, segmento, null)) as distinct_segments_liked_{suffix},
        count(distinct if(liked, genero, null)) as distinct_genres_liked_{suffix},
        count(distinct if(liked, ciudad, null)) as distinct_cities_liked_{suffix},
        0.0 as local_like_rate_{suffix},
        0.0 as local_swipe_share_{suffix},
        coalesce(
            avg(if(liked and fecha_evento is not null, date_diff(fecha_evento, date(event_timestamp), day), null)),
            0.0
        ) as avg_days_until_event_liked_{suffix},
        coalesce(avg(if(liked, price_mid, null)), 0.0) as avg_price_mid_liked_{suffix},
        coalesce(approx_quantiles(if(liked, price_mid, null), 2)[safe_offset(1)], 0.0) as median_price_mid_liked_{suffix},
        coalesce(avg(if(not liked, price_mid, null)), 0.0) as avg_price_mid_disliked_{suffix},
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
            {default_days_since}
        ) as days_since_last_right_swipe_{suffix},
        {segment_preferences},
        {genre_preferences},
        {price_preferences}
    from base
    group by user_id
)

select *
from agg
""".strip()


def dim_sql(project_id: str, intermediate_dataset: str, marts_dataset: str) -> str:
    select_columns: list[str] = ["f90.user_id"]
    for base_name, default in FEATURE_DEFAULTS:
        select_columns.append(f"coalesce(f30.{base_name}_30d, {default}) as {base_name}_30d")
    select_columns.append("coalesce(f30.days_since_last_right_swipe_30d, 37) as days_since_last_right_swipe_30d")
    for prefix in PREFERENCE_PREFIXES:
        for name, _ in SEGMENT_RATES:
            select_columns.append(f"coalesce(f30.{prefix}_segment_{name}_30d, 0.0) as {prefix}_segment_{name}_30d")
        for name, _ in GENRE_RATES:
            select_columns.append(f"coalesce(f30.{prefix}_genre_{name}_30d, 0.0) as {prefix}_genre_{name}_30d")
        for name, _ in PRICE_BANDS:
            select_columns.append(f"coalesce(f30.{prefix}_price_band_{name}_30d, 0.0) as {prefix}_price_band_{name}_30d")

    for base_name, default in FEATURE_DEFAULTS:
        select_columns.append(f"coalesce(f90.{base_name}_90d, {default}) as {base_name}_90d")
    select_columns.append("coalesce(f90.days_since_last_right_swipe_90d, 97) as days_since_last_right_swipe_90d")
    for prefix in PREFERENCE_PREFIXES:
        for name, _ in SEGMENT_RATES:
            select_columns.append(f"coalesce(f90.{prefix}_segment_{name}_90d, 0.0) as {prefix}_segment_{name}_90d")
        for name, _ in GENRE_RATES:
            select_columns.append(f"coalesce(f90.{prefix}_genre_{name}_90d, 0.0) as {prefix}_genre_{name}_90d")
        for name, _ in PRICE_BANDS:
            select_columns.append(f"coalesce(f90.{prefix}_price_band_{name}_90d, 0.0) as {prefix}_price_band_{name}_90d")

    select_columns.append(
        "coalesce(f30.right_swipe_rate_30d, 0.0) - coalesce(f90.right_swipe_rate_90d, 0.0) "
        "as right_swipe_rate_delta_30_vs_90"
    )
    select_columns.append(
        "coalesce(f30.total_swipes_30d, 0) - coalesce(f90.total_swipes_90d, 0) "
        "as total_swipes_delta_30_vs_90"
    )

    rendered_columns = ",\n    ".join(select_columns)
    return f"""
create or replace table {table(project_id, marts_dataset, "dim_user_cluster_features_current")} as
with f30 as (
    select * from {table(project_id, intermediate_dataset, "int_user_swipe_features_30d")}
),

f90 as (
    select * from {table(project_id, intermediate_dataset, "int_user_swipe_features_90d")}
)

select
    {rendered_columns}
from f90
left join f30 using (user_id)
""".strip()


def main() -> None:
    args = parse_args()
    run_bq(args.project_id, staging_sql(args.project_id, args.raw_dataset, args.staging_dataset), "stg_swipes")
    run_bq(args.project_id, fct_sql(args.project_id, args.raw_dataset, args.staging_dataset, args.marts_dataset), "fct_swipes")
    run_bq(
        args.project_id,
        features_sql(args.project_id, args.intermediate_dataset, args.marts_dataset, 30),
        "int_user_swipe_features_30d",
    )
    run_bq(
        args.project_id,
        features_sql(args.project_id, args.intermediate_dataset, args.marts_dataset, 90),
        "int_user_swipe_features_90d",
    )
    run_bq(
        args.project_id,
        dim_sql(args.project_id, args.intermediate_dataset, args.marts_dataset),
        "dim_user_cluster_features_current",
    )
    print("Analytics layer refreshed with bq fallback.")


if __name__ == "__main__":
    main()
