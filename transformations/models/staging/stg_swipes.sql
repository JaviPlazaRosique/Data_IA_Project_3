{{ config(materialized='view') }}

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
    publish_time                                          as ingestion_timestamp
from {{ source('raw', 'swipes_raw') }}
where data is not null
  and json_value(data, '$.event_id')   is not null
  and json_value(data, '$.user_id')    is not null
  and json_value(data, '$.direction')  in ('left', 'right')
  and safe_cast(json_value(data, '$.swiped_at') as timestamp) is not null
