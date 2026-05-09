{{ config(materialized='table') }}

with profile_raw as (
    select
        user_id,
        trim(preferred_location) as preferred_location,
        regexp_replace(normalize(lower(trim(preferred_location)), NFD), r'\pM', '') as preferred_location_key,
        synced_at
    from {{ source('app', 'user_preferences') }}
    where preferred_location is not null
      and trim(preferred_location) != ''
),

profile_preferences as (
    select
        user_id,
        case
            when preferred_location_key in ('madrid', 'madrid capital') then 'Madrid'
            when preferred_location_key in ('barcelona', 'bcn') then 'Barcelona'
            when preferred_location_key in ('valencia', 'valencia ciudad') then 'Valencia'
            when preferred_location_key in ('sevilla', 'seville') then 'Sevilla'
            when preferred_location_key in ('bilbao') then 'Bilbao'
            when preferred_location_key in ('malaga') then 'Malaga'
            else trim(preferred_location)
        end as preferred_city,
        synced_at
    from profile_raw
    qualify row_number() over (
        partition by user_id
        order by synced_at desc nulls last
    ) = 1
),

recent_swipes as (
    select
        user_id,
        case
            when regexp_replace(normalize(lower(trim(ciudad)), NFD), r'\pM', '') in ('madrid', 'madrid capital') then 'Madrid'
            when regexp_replace(normalize(lower(trim(ciudad)), NFD), r'\pM', '') in ('barcelona', 'bcn') then 'Barcelona'
            when regexp_replace(normalize(lower(trim(ciudad)), NFD), r'\pM', '') in ('valencia', 'valencia ciudad') then 'Valencia'
            when regexp_replace(normalize(lower(trim(ciudad)), NFD), r'\pM', '') in ('sevilla', 'seville') then 'Sevilla'
            when regexp_replace(normalize(lower(trim(ciudad)), NFD), r'\pM', '') in ('bilbao') then 'Bilbao'
            when regexp_replace(normalize(lower(trim(ciudad)), NFD), r'\pM', '') in ('malaga') then 'Malaga'
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

ranked_behavior as (
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
),

behavior_city as (
    select
        user_id,
        reference_city,
        if(liked_swipes > 0, 'liked_swipes_90d', 'swipes_90d') as reference_city_source,
        total_swipes as reference_city_swipes_90d,
        liked_swipes as reference_city_likes_90d
    from ranked_behavior
    where city_rank = 1
)

select
    coalesce(profile_preferences.user_id, behavior_city.user_id) as user_id,
    coalesce(profile_preferences.preferred_city, behavior_city.reference_city) as reference_city,
    case
        when profile_preferences.preferred_city is not null then 'preferred_location'
        else behavior_city.reference_city_source
    end as reference_city_source,
    coalesce(behavior_city.reference_city_swipes_90d, 0) as reference_city_swipes_90d,
    coalesce(behavior_city.reference_city_likes_90d, 0) as reference_city_likes_90d
from behavior_city
full outer join profile_preferences
  using (user_id)
