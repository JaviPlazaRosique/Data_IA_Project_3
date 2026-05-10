{{ config(materialized='table') }}

{% set segments = [
    ('music', 'Music'),
    ('sports', 'Sports'),
    ('arts_theatre', 'Arts_Theatre'),
    ('family', 'Family')
] %}

{% set genres = [
    ('rock', 'Rock'),
    ('pop', 'Pop'),
    ('electronic', 'Electronic'),
    ('urban', 'Urban'),
    ('football', 'Football'),
    ('basketball', 'Basketball'),
    ('tennis', 'Tennis'),
    ('theatre', 'Theatre'),
    ('musical', 'Musical'),
    ('comedy', 'Comedy'),
    ('classical', 'Classical'),
    ('kids', 'Kids'),
    ('circus', 'Circus'),
    ('exhibition', 'Exhibition')
] %}

with base as (
    select *
    from {{ ref('fct_swipes') }}
    where event_timestamp >= timestamp_sub(current_timestamp(), interval 30 day)
),

reference_city as (
    select
        user_id,
        reference_city
    from {{ ref('int_user_reference_city') }}
),

agg as (
    select
        base.user_id,
        count(*) as total_swipes_30d,
        countif(liked) as total_right_swipes_30d,
        coalesce(safe_divide(countif(liked), count(*)), 0.0) as right_swipe_rate_30d,
        coalesce(avg(cast(dwell_ms as float64)), 0.0) as avg_dwell_ms_30d,
        coalesce(avg(if(liked, cast(dwell_ms as float64), null)), 0.0) as avg_right_dwell_ms_30d,
        count(distinct if(liked, segmento, null)) as distinct_segments_liked_30d,
        count(distinct if(liked, genero, null)) as distinct_genres_liked_30d,
        count(distinct if(liked, ciudad, null)) as distinct_cities_liked_30d,
        coalesce(safe_divide(countif(liked and ciudad = reference_city.reference_city), countif(liked)), 0.0) as local_like_rate_30d,
        coalesce(safe_divide(countif(ciudad = reference_city.reference_city), count(*)), 0.0) as local_swipe_share_30d,
        coalesce(
            avg(if(liked and fecha_evento is not null, date_diff(fecha_evento, date(event_timestamp), day), null)),
            0.0
        ) as avg_days_until_event_liked_30d,
        coalesce(safe_divide(countif(recommendation_context = 'chat'), count(*)), 0.0) as chat_swipe_share_30d,
        coalesce(
            safe_divide(
                countif(recommendation_context = 'chat' and liked),
                countif(recommendation_context = 'chat')
            ),
            0.0
        ) as chat_right_rate_30d,
        coalesce(
            timestamp_diff(current_timestamp(), max(if(liked, event_timestamp, null)), day),
            37
        ) as days_since_last_right_swipe_30d,
        {% for feature_name, segment_value in segments %}
        coalesce(safe_divide(countif(liked and segmento = '{{ segment_value }}'), countif(segmento = '{{ segment_value }}')), 0.0) as like_rate_segment_{{ feature_name }}_30d,
        coalesce(safe_divide(countif(segmento = '{{ segment_value }}'), count(*)), 0.0) as swipe_share_segment_{{ feature_name }}_30d,
        coalesce(safe_divide(countif(liked and segmento = '{{ segment_value }}'), countif(liked)), 0.0) as liked_share_segment_{{ feature_name }}_30d,
        coalesce(safe_divide(countif(liked and segmento = '{{ segment_value }}'), countif(segmento = '{{ segment_value }}')), 0.0)
            - coalesce(safe_divide(countif(liked), count(*)), 0.0) as preference_lift_segment_{{ feature_name }}_30d,
        {% endfor %}
        {% for feature_name, genre_value in genres %}
        coalesce(safe_divide(countif(liked and genero = '{{ genre_value }}'), countif(genero = '{{ genre_value }}')), 0.0) as like_rate_genre_{{ feature_name }}_30d,
        coalesce(safe_divide(countif(genero = '{{ genre_value }}'), count(*)), 0.0) as swipe_share_genre_{{ feature_name }}_30d,
        coalesce(safe_divide(countif(liked and genero = '{{ genre_value }}'), countif(liked)), 0.0) as liked_share_genre_{{ feature_name }}_30d,
        coalesce(safe_divide(countif(liked and genero = '{{ genre_value }}'), countif(genero = '{{ genre_value }}')), 0.0)
            - coalesce(safe_divide(countif(liked), count(*)), 0.0) as preference_lift_genre_{{ feature_name }}_30d{% if not loop.last %},{% endif %}
        {% endfor %}
    from base
    left join reference_city
      on base.user_id = reference_city.user_id
    group by base.user_id
)

select *
from agg
