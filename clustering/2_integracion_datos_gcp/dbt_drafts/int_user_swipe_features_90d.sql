{{ config(materialized='table') }}

-- Draft generado para clustering.
-- Bloqueos conocidos:
-- 1. `dwell_ms` no esta todavia en stg_swipes/fct_swipes.
-- 2. `precio_min` y `precio_max` llegan como null en fct_swipes.
-- 3. Falta una ciudad de referencia del usuario para features locales.

with base as (
    select *
    from {{ ref('fct_swipes') }}
    where event_timestamp >= timestamp_sub(current_timestamp(), interval 90 day)
),

agg as (
    select
        user_id,
        count(*) as total_swipes_90d,
        countif(liked) as total_right_swipes_90d,
        coalesce(safe_divide(countif(liked), count(*)), 0.0) as right_swipe_rate_90d,
        cast(null as float64) as avg_dwell_ms_90d,
        cast(null as float64) as avg_right_dwell_ms_90d,
        count(distinct if(liked, segmento, null)) as distinct_segments_liked_90d,
        count(distinct if(liked, genero, null)) as distinct_genres_liked_90d,
        count(distinct if(liked, ciudad, null)) as distinct_cities_liked_90d,
        cast(null as float64) as local_like_rate_90d,
        cast(null as float64) as local_swipe_share_90d,
        avg(if(liked and fecha_evento is not null, date_diff(fecha_evento, date(event_timestamp), day), null)) as avg_days_until_event_liked_90d,
        cast(null as float64) as avg_price_mid_liked_90d,
        cast(null as float64) as median_price_mid_liked_90d,
        cast(null as float64) as avg_price_mid_disliked_90d,
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
    coalesce(safe_divide(countif(liked and segmento = 'Music'), countif(segmento = 'Music')), 0.0) as like_rate_segment_music_90d,
    coalesce(safe_divide(countif(liked and segmento = 'Sports'), countif(segmento = 'Sports')), 0.0) as like_rate_segment_sports_90d,
    coalesce(safe_divide(countif(liked and segmento = 'Arts_Theatre'), countif(segmento = 'Arts_Theatre')), 0.0) as like_rate_segment_arts_theatre_90d,
    coalesce(safe_divide(countif(liked and segmento = 'Family'), countif(segmento = 'Family')), 0.0) as like_rate_segment_family_90d,
    coalesce(safe_divide(countif(liked and genero = 'Rock'), countif(genero = 'Rock')), 0.0) as like_rate_genre_rock_90d,
    coalesce(safe_divide(countif(liked and genero = 'Pop'), countif(genero = 'Pop')), 0.0) as like_rate_genre_pop_90d,
    coalesce(safe_divide(countif(liked and genero = 'Electronic'), countif(genero = 'Electronic')), 0.0) as like_rate_genre_electronic_90d,
    coalesce(safe_divide(countif(liked and genero = 'Urban'), countif(genero = 'Urban')), 0.0) as like_rate_genre_urban_90d,
    coalesce(safe_divide(countif(liked and genero = 'Football'), countif(genero = 'Football')), 0.0) as like_rate_genre_football_90d,
    coalesce(safe_divide(countif(liked and genero = 'Basketball'), countif(genero = 'Basketball')), 0.0) as like_rate_genre_basketball_90d,
    coalesce(safe_divide(countif(liked and genero = 'Tennis'), countif(genero = 'Tennis')), 0.0) as like_rate_genre_tennis_90d,
    coalesce(safe_divide(countif(liked and genero = 'Theatre'), countif(genero = 'Theatre')), 0.0) as like_rate_genre_theatre_90d,
    coalesce(safe_divide(countif(liked and genero = 'Musical'), countif(genero = 'Musical')), 0.0) as like_rate_genre_musical_90d,
    coalesce(safe_divide(countif(liked and genero = 'Comedy'), countif(genero = 'Comedy')), 0.0) as like_rate_genre_comedy_90d,
    coalesce(safe_divide(countif(liked and genero = 'Classical'), countif(genero = 'Classical')), 0.0) as like_rate_genre_classical_90d,
    coalesce(safe_divide(countif(liked and genero = 'Kids'), countif(genero = 'Kids')), 0.0) as like_rate_genre_kids_90d,
    coalesce(safe_divide(countif(liked and genero = 'Circus'), countif(genero = 'Circus')), 0.0) as like_rate_genre_circus_90d,
    coalesce(safe_divide(countif(liked and genero = 'Exhibition'), countif(genero = 'Exhibition')), 0.0) as like_rate_genre_exhibition_90d
    from base
    group by user_id
)

select *
from agg
