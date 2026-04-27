{{ config(
    materialized='incremental',
    unique_key='interaction_id',
    partition_by={'field': 'ingestion_timestamp', 'data_type': 'timestamp', 'granularity': 'day'},
    cluster_by=['user_id'],
    incremental_strategy='merge',
    require_partition_filter=true,
    incremental_predicates=[
      "DBT_INTERNAL_DEST.ingestion_timestamp > timestamp_sub(current_timestamp(), interval 3 day)"
    ]
) }}

with swipes as (
    select * from {{ ref('stg_swipes') }}
    {% if is_incremental() %}
      where ingestion_timestamp > timestamp_sub(current_timestamp(), interval 3 day)
        and ingestion_timestamp > (
          select coalesce(max(ingestion_timestamp), timestamp('1970-01-01'))
          from {{ this }}
          where ingestion_timestamp > timestamp_sub(current_timestamp(), interval 3 day)
        )
    {% endif %}
),

eventos as (
    select
        id          as event_id,
        segmento,
        genero,
        subgenero,
        ciudad,
        recinto_id,
        fecha       as fecha_evento
    from {{ source('catalog', 'eventos') }}
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
    d.user_id,
    d.session_id,
    d.event_id,
    d.interaction_type,
    d.swipe_direction,
    d.liked,
    d.recommendation_context,
    e.segmento,
    e.genero,
    e.subgenero,
    e.ciudad,
    cast(null as float64) as precio_min,
    cast(null as float64) as precio_max,
    e.fecha_evento,
    e.recinto_id,
    d.ingestion_timestamp
from dedup d
left join eventos e using (event_id)
where d.rn = 1
