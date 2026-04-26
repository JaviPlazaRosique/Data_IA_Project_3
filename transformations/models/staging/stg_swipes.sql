{{ config(materialized='view') }}

select
    json_value(data, '$.event_id')              as event_id,
    json_value(data, '$.user_id')               as user_id,
    json_value(data, '$.direction')             as direction,
    timestamp(json_value(data, '$.swiped_at'))  as swiped_at,
    publish_time                                 as ingested_at,
    message_id
from {{ source('raw', 'swipes_raw') }}
where data is not null
  and json_value(data, '$.event_id')  is not null
  and json_value(data, '$.user_id')   is not null
  and json_value(data, '$.direction') is not null
  and json_value(data, '$.swiped_at') is not null
