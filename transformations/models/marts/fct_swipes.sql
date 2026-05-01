{{ config(
    materialized='incremental',
    unique_key='interaction_id',
    partition_by={'field': 'ingestion_timestamp', 'data_type': 'timestamp', 'granularity': 'day'},
    cluster_by=['user_id'],
    incremental_strategy='merge',
    require_partition_filter=true,
    incremental_predicates=[
      "DBT_INTERNAL_DEST.ingestion_timestamp > timestamp_sub(current_timestamp(), interval 7 day)"
    ],
    post_hook="DELETE FROM {{ this }} WHERE ingestion_timestamp < timestamp_sub(current_timestamp(), interval 365 day)"
) }}

{% set retention_days = var('retention_days', 365) %}
{% set lookback_days  = var('lookback_days', 7) %}

with swipes as (
    select * from {{ ref('stg_swipes') }}
    where ingestion_timestamp > timestamp_sub(current_timestamp(), interval {{ retention_days }} day)
    {% if is_incremental() %}
      and ingestion_timestamp > timestamp_sub(current_timestamp(), interval {{ lookback_days }} day)
      and ingestion_timestamp > (
        select coalesce(max(ingestion_timestamp), timestamp('1970-01-01'))
        from {{ this }}
        where ingestion_timestamp > timestamp_sub(current_timestamp(), interval {{ lookback_days }} day)
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
        fecha       as fecha_evento,
        banda_precio
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
    d.snapshot_precio_min as precio_min,
    d.snapshot_precio_max as precio_max,
    coalesce(d.snapshot_banda_precio, e.banda_precio) as banda_precio,
    coalesce(d.snapshot_fecha_evento, e.fecha_evento) as fecha_evento,
    coalesce(d.snapshot_recinto_id, e.recinto_id) as recinto_id,
    d.ingestion_timestamp
from dedup d
left join eventos e using (event_id)
where d.rn = 1
