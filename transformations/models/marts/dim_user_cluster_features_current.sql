{{ config(materialized='table') }}

{% set feature_defaults = [
    ('total_swipes', '0'),
    ('total_right_swipes', '0'),
    ('right_swipe_rate', '0.0'),
    ('avg_dwell_ms', '0.0'),
    ('avg_right_dwell_ms', '0.0'),
    ('distinct_segments_liked', '0'),
    ('distinct_genres_liked', '0'),
    ('distinct_cities_liked', '0'),
    ('local_like_rate', '0.0'),
    ('local_swipe_share', '0.0'),
    ('avg_days_until_event_liked', '0.0'),
    ('chat_swipe_share', '0.0'),
    ('chat_right_rate', '0.0')
] %}

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

{% set preference_prefixes = [
    'like_rate',
    'swipe_share',
    'liked_share',
    'preference_lift'
] %}

with f30 as (
    select * from {{ ref('int_user_swipe_features_30d') }}
),

f90 as (
    select * from {{ ref('int_user_swipe_features_90d') }}
),

reference_city as (
    select * from {{ ref('int_user_reference_city') }}
)

select
    f90.user_id,
    reference_city.reference_city,
    reference_city.reference_city as home_city,
    reference_city.reference_city_source,
    coalesce(reference_city.reference_city_swipes_90d, 0) as reference_city_swipes_90d,
    coalesce(reference_city.reference_city_likes_90d, 0) as reference_city_likes_90d,
    {% for base_name, default in feature_defaults %}
    coalesce(f30.{{ base_name }}_30d, {{ default }}) as {{ base_name }}_30d,
    {% endfor %}
    coalesce(f30.days_since_last_right_swipe_30d, 37) as days_since_last_right_swipe_30d,
    {% for prefix in preference_prefixes %}
        {% for feature_name, _ in segments %}
    coalesce(f30.{{ prefix }}_segment_{{ feature_name }}_30d, 0.0) as {{ prefix }}_segment_{{ feature_name }}_30d,
        {% endfor %}
        {% for feature_name, _ in genres %}
    coalesce(f30.{{ prefix }}_genre_{{ feature_name }}_30d, 0.0) as {{ prefix }}_genre_{{ feature_name }}_30d,
        {% endfor %}
    {% endfor %}
    {% for base_name, default in feature_defaults %}
    coalesce(f90.{{ base_name }}_90d, {{ default }}) as {{ base_name }}_90d,
    {% endfor %}
    coalesce(f90.days_since_last_right_swipe_90d, 97) as days_since_last_right_swipe_90d,
    {% for prefix in preference_prefixes %}
        {% for feature_name, _ in segments %}
    coalesce(f90.{{ prefix }}_segment_{{ feature_name }}_90d, 0.0) as {{ prefix }}_segment_{{ feature_name }}_90d,
        {% endfor %}
        {% for feature_name, _ in genres %}
    coalesce(f90.{{ prefix }}_genre_{{ feature_name }}_90d, 0.0) as {{ prefix }}_genre_{{ feature_name }}_90d,
        {% endfor %}
    {% endfor %}
    coalesce(f30.right_swipe_rate_30d, 0.0) - coalesce(f90.right_swipe_rate_90d, 0.0) as right_swipe_rate_delta_30_vs_90,
    coalesce(f30.total_swipes_30d, 0) - coalesce(f90.total_swipes_90d, 0) as total_swipes_delta_30_vs_90
from f90
left join f30 using (user_id)
left join reference_city using (user_id)
