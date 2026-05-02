from __future__ import annotations

import argparse
import subprocess

from serving_config import (
    DEFAULT_LOOKBACK_DAYS,
    DEFAULT_MARTS_DATASET,
    DEFAULT_MODEL_RUN_ID,
    DEFAULT_PROJECT_ID,
    safe_sql_literal,
    table,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build cluster affinity by event taxonomy from historical swipes.")
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--marts-dataset", default=DEFAULT_MARTS_DATASET)
    parser.add_argument("--model-run-id", default=DEFAULT_MODEL_RUN_ID)
    parser.add_argument("--lookback-days", type=int, default=DEFAULT_LOOKBACK_DAYS)
    return parser.parse_args()


def run_query(project_id: str, sql: str) -> None:
    subprocess.run(
        [
            "bq",
            "query",
            f"--project_id={project_id}",
            "--use_legacy_sql=false",
            "--quiet",
            sql,
        ],
        check=True,
    )


def swipe_segment_expression() -> str:
    return """
case
  when s.segmento in ('Music', 'Sports', 'Family', 'Arts_Theatre') then s.segmento
  when s.segmento = 'Arts & Theatre' then 'Arts_Theatre'
  when s.segmento = 'Miscellaneous' and s.genero = 'Family' then 'Family'
  else coalesce(s.segmento, 'Unknown')
end
""".strip()


def swipe_genre_expression() -> str:
    return """
case
  when s.genero in (
    'Rock', 'Pop', 'Electronic', 'Urban', 'Football', 'Basketball', 'Tennis',
    'Theatre', 'Musical', 'Comedy', 'Classical', 'Kids', 'Circus', 'Exhibition'
  ) then s.genero
  when s.genero = 'Alternative' then 'Rock'
  when s.genero in ('World', 'Latin') then 'Pop'
  when s.genero = 'Cultural' then 'Theatre'
  when s.genero = 'Family' then 'Exhibition'
  else coalesce(s.genero, 'Unknown')
end
""".strip()


def build_sql(project_id: str, marts_dataset: str, model_run_id: str, lookback_days: int) -> str:
    escaped_run_id = safe_sql_literal(model_run_id)
    assignments = table(project_id, marts_dataset, "user_cluster_assignments")
    fct_swipes = table(project_id, marts_dataset, "fct_swipes")
    output_table = table(project_id, marts_dataset, "cluster_event_affinity")
    segment_expr = swipe_segment_expression()
    genre_expr = swipe_genre_expression()

    return f"""
create or replace table {output_table}
cluster by cluster_id, segmento, genero as
with clustered_swipes as (
  select
    a.cluster_id,
    {segment_expr} as segmento,
    {genre_expr} as genero,
    coalesce(lower(s.banda_precio), 'unknown') as banda_precio,
    s.liked
  from {fct_swipes} s
  inner join {assignments} a
    using (user_id)
  where s.event_timestamp >= timestamp_sub(current_timestamp(), interval {lookback_days} day)
),

cluster_totals as (
  select
    cluster_id,
    count(*) as cluster_swipes,
    countif(liked) as cluster_likes,
    safe_divide(countif(liked), count(*)) as cluster_like_rate
  from clustered_swipes
  group by cluster_id
),

global_taxonomy as (
  select
    segmento,
    genero,
    banda_precio,
    count(*) as global_swipes,
    countif(liked) as global_likes,
    safe_divide(countif(liked), count(*)) as global_like_rate
  from clustered_swipes
  group by segmento, genero, banda_precio
),

taxonomy_affinity as (
  select
    s.cluster_id,
    s.segmento,
    s.genero,
    s.banda_precio,
    count(*) as swipe_count,
    countif(s.liked) as like_count,
    safe_divide(countif(s.liked), count(*)) as like_rate,
    safe_divide(count(*), any_value(t.cluster_swipes)) as exposure_share,
    safe_divide(countif(s.liked), any_value(t.cluster_likes)) as liked_share,
    any_value(t.cluster_like_rate) as cluster_like_rate,
    any_value(g.global_like_rate) as global_like_rate
  from clustered_swipes s
  inner join cluster_totals t
    using (cluster_id)
  left join global_taxonomy g
    using (segmento, genero, banda_precio)
  group by s.cluster_id, s.segmento, s.genero, s.banda_precio
)

select
  '{escaped_run_id}' as model_run_id,
  current_timestamp() as computed_at,
  cluster_id,
  segmento,
  genero,
  banda_precio,
  swipe_count,
  like_count,
  like_rate,
  exposure_share,
  liked_share,
  cluster_like_rate,
  global_like_rate,
  like_rate - cluster_like_rate as cluster_preference_lift,
  like_rate - global_like_rate as global_preference_lift,
  (
    0.40 * coalesce(liked_share, 0.0)
    + 0.25 * coalesce(exposure_share, 0.0)
    + 0.25 * greatest(coalesce(like_rate - cluster_like_rate, 0.0), 0.0)
    + 0.10 * greatest(coalesce(like_rate - global_like_rate, 0.0), 0.0)
  ) as affinity_score
from taxonomy_affinity
where swipe_count >= 3
""".strip()


def main() -> None:
    args = parse_args()
    run_query(args.project_id, build_sql(args.project_id, args.marts_dataset, args.model_run_id, args.lookback_days))
    print(f"Built {args.project_id}.{args.marts_dataset}.cluster_event_affinity")


if __name__ == "__main__":
    main()
