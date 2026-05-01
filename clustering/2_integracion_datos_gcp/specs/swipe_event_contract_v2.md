# Contrato enriquecido del swipe (`v2`)

## Objetivo

Evitar que el clustering dependa exclusivamente de joins posteriores y guardar el contexto del evento en el momento exacto de la interaccion.

## Cambios principales frente al payload actual

- se anade `schema_version`;
- se mantiene el payload base actual (`event_id`, `direction`, `swiped_at`, `dwell_ms`, `session_id`, `recommendation_context`);
- se anade `rank_position` para capturar contexto de ranking;
- se anade `recommendation_id` para trazabilidad de la recomendacion;
- se anade `producer` para identificar superficie y version del cliente;
- se anade `event_snapshot` con metadatos del evento.

## Campos recomendados del snapshot

- `segmento`
- `genero`
- `subgenero`
- `ciudad`
- `recinto_id`
- `fecha_evento`
- `precio_min`
- `precio_max`
- `banda_precio`

## Racional analitico

- `dwell_ms`: engagement real del usuario.
- `rank_position`: sesgo por posicion en el deck.
- `event_snapshot`: protege de cambios posteriores en el catalogo.
- `banda_precio`: alternativa temporal mientras no haya precio numerico estable.

## Implementacion recomendada

1. Frontend:
   ampliar `SwipeEventCreate` en `frontend/portal/src/api.ts`.
2. Frontend:
   enviar `event_snapshot` desde `frontend/portal/src/components/QuickMatch.tsx`.
3. Backend:
   ampliar `SwipeEventCreate` en `backend/portal-api/app/schemas/saved_event.py`.
4. Staging dbt:
   parsear `event_snapshot.*` en `transformations/models/staging/stg_swipes.sql`.
5. Mart dbt:
   hacer que `fct_swipes` prefiera el snapshot del payload cuando exista, y use join al catalogo como fallback.
