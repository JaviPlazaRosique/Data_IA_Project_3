{{ config(materialized='view') }}

select
    message_id                                            as interaction_id,
    timestamp(json_value(data, '$.swiped_at'))            as event_timestamp,
    json_value(data, '$.user_id')                         as user_id,
    json_value(data, '$.session_id')                      as session_id,
    json_value(data, '$.event_id')                        as event_id,
    coalesce(json_value(data, '$.interaction_type'), 'swipe') as interaction_type,
    json_value(data, '$.direction')                       as swipe_direction,
    case json_value(data, '$.direction')
        when 'right' then true
        when 'left'  then false
    end                                                   as liked,
    json_value(data, '$.recommendation_context')          as recommendation_context,
    publish_time                                          as ingestion_timestamp
from {{ source('raw', 'swipes_raw') }}
where data is not null
  and json_value(data, '$.event_id')   is not null
  and json_value(data, '$.user_id')    is not null
  and json_value(data, '$.direction')  is not null
  and json_value(data, '$.swiped_at')  is not null
