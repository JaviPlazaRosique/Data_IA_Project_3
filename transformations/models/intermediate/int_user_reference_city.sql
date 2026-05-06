{{ config(materialized='table') }}

with recent_swipes as (
    select
        user_id,
        case
            when lower(trim(ciudad)) in ('madrid', 'madrid capital') then 'Madrid'
            when lower(trim(ciudad)) in ('barcelona', 'bcn') then 'Barcelona'
            when lower(trim(ciudad)) in ('valencia', 'valencia ciudad') then 'Valencia'
            when lower(trim(ciudad)) in ('sevilla', 'seville') then 'Sevilla'
            when lower(trim(ciudad)) in ('bilbao') then 'Bilbao'
            when lower(trim(ciudad)) in ('malaga', 'málaga') then 'Malaga'
            else trim(ciudad)
        end as normalized_city,
        liked,
        event_timestamp
    from {{ ref('fct_swipes') }}
    where event_timestamp >= timestamp_sub(current_timestamp(), interval 90 day)
      and ciudad is not null
      and trim(ciudad) != ''
),

city_counts as (
    select
        user_id,
        normalized_city as reference_city,
        count(*) as total_swipes,
        countif(liked) as liked_swipes,
        max(event_timestamp) as latest_swipe_at
    from recent_swipes
    group by user_id, reference_city
),

ranked as (
    select
        *,
        row_number() over (
            partition by user_id
            order by
                if(liked_swipes > 0, 0, 1),
                liked_swipes desc,
                total_swipes desc,
                latest_swipe_at desc,
                reference_city asc
        ) as city_rank
    from city_counts
)

select
    user_id,
    reference_city,
    if(liked_swipes > 0, 'liked_swipes_90d', 'swipes_90d') as reference_city_source,
    total_swipes as reference_city_swipes_90d,
    liked_swipes as reference_city_likes_90d
from ranked
where city_rank = 1
