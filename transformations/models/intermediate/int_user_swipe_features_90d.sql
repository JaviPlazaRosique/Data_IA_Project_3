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

{% set price_bands = [
    ('low', 'bajo'),
    ('medium', 'medio'),
    ('high', 'alto')
] %}

with base as (
    select
        *,
        coalesce(
            case
                when precio_min is not null and precio_max is not null
                    then (precio_min + precio_max) / 2.0
            end,
            price_proxy_mid
        ) as price_mid
    from {{ ref('fct_swipes') }}
    where event_timestamp >= timestamp_sub(current_timestamp(), interval 90 day)
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
        count(*) as total_swipes_90d,
        countif(liked) as total_right_swipes_90d,
        coalesce(safe_divide(countif(liked), count(*)), 0.0) as right_swipe_rate_90d,
        coalesce(avg(cast(dwell_ms as float64)), 0.0) as avg_dwell_ms_90d,
        coalesce(avg(if(liked, cast(dwell_ms as float64), null)), 0.0) as avg_right_dwell_ms_90d,
        count(distinct if(liked, segmento, null)) as distinct_segments_liked_90d,
        count(distinct if(liked, genero, null)) as distinct_genres_liked_90d,
        count(distinct if(liked, ciudad, null)) as distinct_cities_liked_90d,
        coalesce(safe_divide(countif(liked and ciudad = reference_city.reference_city), countif(liked)), 0.0) as local_like_rate_90d,
        coalesce(safe_divide(countif(ciudad = reference_city.reference_city), count(*)), 0.0) as local_swipe_share_90d,
        coalesce(
            avg(if(liked and fecha_evento is not null, date_diff(fecha_evento, date(event_timestamp), day), null)),
            0.0
        ) as avg_days_until_event_liked_90d,
        coalesce(avg(if(liked, price_mid, null)), 0.0) as avg_price_mid_liked_90d,
        coalesce(approx_quantiles(if(liked, price_mid, null), 2)[safe_offset(1)], 0.0) as median_price_mid_liked_90d,
        coalesce(avg(if(not liked, price_mid, null)), 0.0) as avg_price_mid_disliked_90d,
        coalesce(safe_divide(countif(recommendation_context = 'chat'), count(*)), 0.0) as chat_swipe_share_90d,
        coalesce(
            safe_divide(
                countif(recommendation_context = 'chat' and liked),
                countif(recommendation_context = 'chat')
            ),
            0.0
        ) as chat_right_rate_90d,
        coalesce(
            timestamp_diff(current_timestamp(), max(if(liked, event_timestamp, null)), day),
            97
        ) as days_since_last_right_swipe_90d,
        {% for feature_name, segment_value in segments %}
        coalesce(safe_divide(countif(liked and segmento = '{{ segment_value }}'), countif(segmento = '{{ segment_value }}')), 0.0) as like_rate_segment_{{ feature_name }}_90d,
        coalesce(safe_divide(countif(segmento = '{{ segment_value }}'), count(*)), 0.0) as swipe_share_segment_{{ feature_name }}_90d,
        coalesce(safe_divide(countif(liked and segmento = '{{ segment_value }}'), countif(liked)), 0.0) as liked_share_segment_{{ feature_name }}_90d,
        coalesce(safe_divide(countif(liked and segmento = '{{ segment_value }}'), countif(segmento = '{{ segment_value }}')), 0.0)
            - coalesce(safe_divide(countif(liked), count(*)), 0.0) as preference_lift_segment_{{ feature_name }}_90d,
        {% endfor %}
        {% for feature_name, genre_value in genres %}
        coalesce(safe_divide(countif(liked and genero = '{{ genre_value }}'), countif(genero = '{{ genre_value }}')), 0.0) as like_rate_genre_{{ feature_name }}_90d,
        coalesce(safe_divide(countif(genero = '{{ genre_value }}'), count(*)), 0.0) as swipe_share_genre_{{ feature_name }}_90d,
        coalesce(safe_divide(countif(liked and genero = '{{ genre_value }}'), countif(liked)), 0.0) as liked_share_genre_{{ feature_name }}_90d,
        coalesce(safe_divide(countif(liked and genero = '{{ genre_value }}'), countif(genero = '{{ genre_value }}')), 0.0)
            - coalesce(safe_divide(countif(liked), count(*)), 0.0) as preference_lift_genre_{{ feature_name }}_90d,
        {% endfor %}
        {% for feature_name, band_value in price_bands %}
        coalesce(safe_divide(countif(liked and lower(banda_precio) = '{{ band_value }}'), countif(lower(banda_precio) = '{{ band_value }}')), 0.0) as like_rate_price_band_{{ feature_name }}_90d,
        coalesce(safe_divide(countif(lower(banda_precio) = '{{ band_value }}'), count(*)), 0.0) as swipe_share_price_band_{{ feature_name }}_90d,
        coalesce(safe_divide(countif(liked and lower(banda_precio) = '{{ band_value }}'), countif(liked)), 0.0) as liked_share_price_band_{{ feature_name }}_90d,
        coalesce(safe_divide(countif(liked and lower(banda_precio) = '{{ band_value }}'), countif(lower(banda_precio) = '{{ band_value }}')), 0.0)
            - coalesce(safe_divide(countif(liked), count(*)), 0.0) as preference_lift_price_band_{{ feature_name }}_90d{% if not loop.last %},{% endif %}
        {% endfor %}
    from base
    left join reference_city
      on base.user_id = reference_city.user_id
    group by base.user_id
)

select *
from agg
