from __future__ import annotations

import argparse
import subprocess

from serving_config import (
    DEFAULT_MARTS_DATASET,
    DEFAULT_MAX_RECOMMENDATIONS_PER_USER,
    DEFAULT_MODEL_RUN_ID,
    DEFAULT_NEIGHBOR_COUNT,
    DEFAULT_PROJECT_ID,
    DEFAULT_RAW_DATASET,
    safe_sql_literal,
    table,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate user recommendation candidates from cluster affinity.")
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--raw-dataset", default=DEFAULT_RAW_DATASET)
    parser.add_argument("--marts-dataset", default=DEFAULT_MARTS_DATASET)
    parser.add_argument("--model-run-id", default=DEFAULT_MODEL_RUN_ID)
    parser.add_argument("--neighbor-count", type=int, default=DEFAULT_NEIGHBOR_COUNT)
    parser.add_argument("--max-per-user", type=int, default=DEFAULT_MAX_RECOMMENDATIONS_PER_USER)
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


def event_segment_expression() -> str:
    return """
case
  when lower(concat(coalesce(e.segmento, ''), ' ', coalesce(e.genero, ''), ' ', coalesce(e.subgenero, ''), ' ', coalesce(e.categoria, ''), ' ', coalesce(e.subcategoria, ''))) like '%deporte%'
    or e.segmento = 'Sports' then 'Sports'
  when lower(concat(coalesce(e.segmento, ''), ' ', coalesce(e.genero, ''), ' ', coalesce(e.subgenero, ''), ' ', coalesce(e.categoria, ''), ' ', coalesce(e.subcategoria, ''))) like '%familia%'
    or e.segmento = 'Miscellaneous'
    or e.genero = 'Family' then 'Family'
  when lower(concat(coalesce(e.segmento, ''), ' ', coalesce(e.genero, ''), ' ', coalesce(e.subgenero, ''), ' ', coalesce(e.categoria, ''), ' ', coalesce(e.subcategoria, ''))) like '%arte y teatro%'
    or lower(e.segmento) = 'arts & theatre' then 'Arts_Theatre'
  when lower(concat(coalesce(e.segmento, ''), ' ', coalesce(e.genero, ''), ' ', coalesce(e.subgenero, ''), ' ', coalesce(e.categoria, ''), ' ', coalesce(e.subcategoria, ''))) like '%musica%'
    or lower(concat(coalesce(e.segmento, ''), ' ', coalesce(e.genero, ''), ' ', coalesce(e.subgenero, ''), ' ', coalesce(e.categoria, ''), ' ', coalesce(e.subcategoria, ''))) like '%música%'
    or e.segmento = 'Music' then 'Music'
  else 'Arts_Theatre'
end
""".strip()


def event_genre_expression() -> str:
    return """
case
  when lower(concat(coalesce(e.segmento, ''), ' ', coalesce(e.genero, ''), ' ', coalesce(e.subgenero, ''), ' ', coalesce(e.categoria, ''), ' ', coalesce(e.subcategoria, ''))) like '%basket%'
    or lower(concat(coalesce(e.segmento, ''), ' ', coalesce(e.genero, ''), ' ', coalesce(e.subgenero, ''), ' ', coalesce(e.categoria, ''), ' ', coalesce(e.subcategoria, ''))) like '%baloncesto%' then 'Basketball'
  when lower(concat(coalesce(e.segmento, ''), ' ', coalesce(e.genero, ''), ' ', coalesce(e.subgenero, ''), ' ', coalesce(e.categoria, ''), ' ', coalesce(e.subcategoria, ''))) like '%circo%' then 'Circus'
  when lower(concat(coalesce(e.segmento, ''), ' ', coalesce(e.genero, ''), ' ', coalesce(e.subgenero, ''), ' ', coalesce(e.categoria, ''), ' ', coalesce(e.subcategoria, ''))) like '%parque%'
    or lower(concat(coalesce(e.segmento, ''), ' ', coalesce(e.genero, ''), ' ', coalesce(e.subgenero, ''), ' ', coalesce(e.categoria, ''), ' ', coalesce(e.subcategoria, ''))) like '%infantil%'
    or lower(concat(coalesce(e.segmento, ''), ' ', coalesce(e.genero, ''), ' ', coalesce(e.subgenero, ''), ' ', coalesce(e.categoria, ''), ' ', coalesce(e.subcategoria, ''))) like '%kids%' then 'Kids'
  when lower(concat(coalesce(e.segmento, ''), ' ', coalesce(e.genero, ''), ' ', coalesce(e.subgenero, ''), ' ', coalesce(e.categoria, ''), ' ', coalesce(e.subcategoria, ''))) like '%expos%' then 'Exhibition'
  when lower(concat(coalesce(e.segmento, ''), ' ', coalesce(e.genero, ''), ' ', coalesce(e.subgenero, ''), ' ', coalesce(e.categoria, ''), ' ', coalesce(e.subcategoria, ''))) like '%comedia%' then 'Comedy'
  when lower(concat(coalesce(e.segmento, ''), ' ', coalesce(e.genero, ''), ' ', coalesce(e.subgenero, ''), ' ', coalesce(e.categoria, ''), ' ', coalesce(e.subcategoria, ''))) like '%musical%' then 'Musical'
  when lower(concat(coalesce(e.segmento, ''), ' ', coalesce(e.genero, ''), ' ', coalesce(e.subgenero, ''), ' ', coalesce(e.categoria, ''), ' ', coalesce(e.subcategoria, ''))) like '%ballet%'
    or lower(concat(coalesce(e.segmento, ''), ' ', coalesce(e.genero, ''), ' ', coalesce(e.subgenero, ''), ' ', coalesce(e.categoria, ''), ' ', coalesce(e.subcategoria, ''))) like '%danza%'
    or lower(concat(coalesce(e.segmento, ''), ' ', coalesce(e.genero, ''), ' ', coalesce(e.subgenero, ''), ' ', coalesce(e.categoria, ''), ' ', coalesce(e.subcategoria, ''))) like '%cultural%' then 'Theatre'
  when e.genero in ('Rock', 'Alternative')
    or lower(concat(coalesce(e.segmento, ''), ' ', coalesce(e.genero, ''), ' ', coalesce(e.subgenero, ''), ' ', coalesce(e.categoria, ''), ' ', coalesce(e.subcategoria, ''))) like '%rock%'
    or lower(concat(coalesce(e.segmento, ''), ' ', coalesce(e.genero, ''), ' ', coalesce(e.subgenero, ''), ' ', coalesce(e.categoria, ''), ' ', coalesce(e.subcategoria, ''))) like '%indie%' then 'Rock'
  when e.genero = 'Pop'
    or lower(concat(coalesce(e.segmento, ''), ' ', coalesce(e.genero, ''), ' ', coalesce(e.subgenero, ''), ' ', coalesce(e.categoria, ''), ' ', coalesce(e.subcategoria, ''))) like '%pop%'
    or lower(concat(coalesce(e.segmento, ''), ' ', coalesce(e.genero, ''), ' ', coalesce(e.subgenero, ''), ' ', coalesce(e.categoria, ''), ' ', coalesce(e.subcategoria, ''))) like '%latin%'
    or lower(concat(coalesce(e.segmento, ''), ' ', coalesce(e.genero, ''), ' ', coalesce(e.subgenero, ''), ' ', coalesce(e.categoria, ''), ' ', coalesce(e.subcategoria, ''))) like '%flamenco%'
    or lower(concat(coalesce(e.segmento, ''), ' ', coalesce(e.genero, ''), ' ', coalesce(e.subgenero, ''), ' ', coalesce(e.categoria, ''), ' ', coalesce(e.subcategoria, ''))) like '%world%' then 'Pop'
  else 'Theatre'
end
""".strip()


def build_sql(
    project_id: str,
    raw_dataset: str,
    marts_dataset: str,
    model_run_id: str,
    neighbor_count: int,
    max_per_user: int,
) -> str:
    escaped_run_id = safe_sql_literal(model_run_id)
    assignments = table(project_id, marts_dataset, "user_cluster_assignments")
    neighbors = table(project_id, marts_dataset, "cluster_neighbors")
    affinity = table(project_id, marts_dataset, "cluster_event_affinity")
    fct_swipes = table(project_id, marts_dataset, "fct_swipes")
    eventos = table(project_id, raw_dataset, "eventos")
    output_table = table(project_id, marts_dataset, "user_recommendation_candidates")

    segment_expr = event_segment_expression()
    genre_expr = event_genre_expression()

    return f"""
create or replace table {output_table}
partition by date(computed_at)
cluster by user_id, recommendation_rank as
with recommendation_clusters as (
  select
    cluster_id as user_cluster_id,
    cluster_id as recommendation_cluster_id,
    1 as cluster_rank,
    1.0 as cluster_weight,
    'own_cluster' as cluster_source
  from {assignments}
  group by cluster_id

  union all

  select
    cluster_id as user_cluster_id,
    neighbor_cluster_id as recommendation_cluster_id,
    neighbor_rank + 1 as cluster_rank,
    case neighbor_rank
      when 1 then 0.60
      when 2 then 0.40
      else 0.25
    end as cluster_weight,
    'neighbor_cluster' as cluster_source
  from {neighbors}
  where neighbor_rank <= {neighbor_count}
),

event_catalog as (
  select
    e.id as event_id,
    e.nombre as event_name,
    e.fecha as fecha_evento,
    e.ciudad,
    e.recinto_id,
    e.recinto_nombre,
    {segment_expr} as segmento,
    {genre_expr} as genero,
    coalesce(e.subgenero, e.subcategoria, 'Unknown') as subgenero,
    coalesce(lower(e.banda_precio), 'unknown') as banda_precio,
    e.banda_precio as banda_precio_original,
    coalesce(
      case lower(e.banda_precio)
        when 'bajo' then 15.0
        when 'medio' then 45.0
        when 'alto' then 90.0
      end,
      45.0
    ) as price_proxy_mid
  from {eventos} e
  where e.id is not null
    and e.fecha is not null
    and e.fecha >= date_sub(current_date(), interval 1 day)
),

seen_events as (
  select distinct user_id, event_id
  from {fct_swipes}
),

scored_candidates as (
  select
    a.user_id,
    a.cluster_id as user_cluster_id,
    rc.recommendation_cluster_id,
    rc.cluster_source,
    rc.cluster_rank,
    rc.cluster_weight,
    e.event_id,
    e.event_name,
    e.fecha_evento,
    e.ciudad,
    e.recinto_id,
    e.recinto_nombre,
    e.segmento,
    e.genero,
    e.subgenero,
    e.banda_precio_original as banda_precio,
    e.price_proxy_mid,
    coalesce(aff.affinity_score, 0.0) as affinity_score,
    coalesce(aff.like_rate, 0.0) as cluster_like_rate_for_event_type,
    coalesce(aff.liked_share, 0.0) as cluster_liked_share_for_event_type,
    if(coalesce(a.reference_city, a.home_city) is not null and lower(coalesce(a.reference_city, a.home_city)) = lower(e.ciudad), 0.08, 0.0) as home_city_boost,
    greatest(0.0, 0.04 - (date_diff(e.fecha_evento, current_date(), day) * 0.002)) as urgency_boost,
    (
      rc.cluster_weight * coalesce(aff.affinity_score, 0.0)
      + if(coalesce(a.reference_city, a.home_city) is not null and lower(coalesce(a.reference_city, a.home_city)) = lower(e.ciudad), 0.08, 0.0)
      + greatest(0.0, 0.04 - (date_diff(e.fecha_evento, current_date(), day) * 0.002))
    ) as recommendation_score
  from {assignments} a
  inner join recommendation_clusters rc
    on a.cluster_id = rc.user_cluster_id
  cross join event_catalog e
  left join {affinity} aff
    on aff.cluster_id = rc.recommendation_cluster_id
   and aff.segmento = e.segmento
   and aff.genero = e.genero
   and aff.banda_precio = e.banda_precio
  left join seen_events seen
    on seen.user_id = a.user_id
   and seen.event_id = e.event_id
  where seen.event_id is null
),

best_contribution as (
  select *
  from scored_candidates
  qualify row_number() over (
    partition by user_id, event_id
    order by recommendation_score desc, cluster_weight desc, cluster_rank asc
  ) = 1
),

ranked as (
  select
    *,
    row_number() over (
      partition by user_id
      order by recommendation_score desc, fecha_evento asc, event_id asc
    ) as recommendation_rank
  from best_contribution
)

select
  '{escaped_run_id}' as model_run_id,
  current_timestamp() as computed_at,
  user_id,
  user_cluster_id,
  recommendation_rank,
  event_id,
  event_name,
  fecha_evento,
  ciudad,
  recinto_id,
  recinto_nombre,
  segmento,
  genero,
  subgenero,
  banda_precio,
  price_proxy_mid,
  recommendation_cluster_id,
  cluster_source,
  cluster_rank,
  cluster_weight,
  affinity_score,
  cluster_like_rate_for_event_type,
  cluster_liked_share_for_event_type,
  home_city_boost,
  urgency_boost,
  recommendation_score
from ranked
where recommendation_rank <= {max_per_user}
""".strip()


def main() -> None:
    args = parse_args()
    run_query(
        args.project_id,
        build_sql(
            args.project_id,
            args.raw_dataset,
            args.marts_dataset,
            args.model_run_id,
            args.neighbor_count,
            args.max_per_user,
        ),
    )
    print(f"Built {args.project_id}.{args.marts_dataset}.user_recommendation_candidates")


if __name__ == "__main__":
    main()
