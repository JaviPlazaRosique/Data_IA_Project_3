{{ config(
    materialized='incremental',
    unique_key='message_id',
    partition_by={'field': 'ingested_at', 'data_type': 'timestamp', 'granularity': 'day'},
    cluster_by=['user_id'],
    incremental_strategy='merge',
    require_partition_filter=true,
    incremental_predicates=[
      "DBT_INTERNAL_DEST.ingested_at > timestamp_sub(current_timestamp(), interval 3 day)"
    ]
) }}

with swipes as (
    select * from {{ ref('stg_swipes') }}
    {% if is_incremental() %}
      where ingested_at > timestamp_sub(current_timestamp(), interval 3 day)
        and ingested_at > (
          select coalesce(max(ingested_at), timestamp('1970-01-01'))
          from {{ this }}
          where ingested_at > timestamp_sub(current_timestamp(), interval 3 day)
        )
    {% endif %}
),

eventos as (
    select
        id              as event_id,
        nombre          as event_nombre,
        ciudad          as event_ciudad,
        genero          as event_genero,
        subgenero       as event_subgenero,
        recinto_nombre  as event_recinto
    from {{ source('catalog', 'eventos') }}
),

dedup as (
    select
        s.*,
        row_number() over (partition by message_id order by ingested_at desc) as rn
    from swipes s
)

select
    d.event_id,
    d.user_id,
    d.direction,
    d.swiped_at,
    d.ingested_at,
    d.message_id,
    e.event_nombre,
    e.event_ciudad,
    e.event_genero,
    e.event_subgenero,
    e.event_recinto
from dedup d
left join eventos e using (event_id)
where d.rn = 1
