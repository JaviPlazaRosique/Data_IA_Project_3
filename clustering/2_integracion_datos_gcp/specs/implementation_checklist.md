# Checklist de implementación del contrato de swipe v2

## Frontend

- completado: actualizar el tipo `SwipeEventCreate` en `frontend/portal/src/api.ts`;
- completado: enviar `schema_version`, `rank_position`, `producer` y `event_snapshot`;
- completado: asegurar que `QuickMatch` tenga acceso al evento visible completo al publicar el swipe.

## Backend

- completado: ampliar el schema Pydantic de `SwipeEventCreate`;
- completado: validar tipos y opcionales;
- completado: mantener compatibilidad hacia atras con `v1` durante la transición.

## dbt / BigQuery

- completado: parsear en `stg_swipes`:
  - `event_snapshot.segmento`
  - `event_snapshot.genero`
  - `event_snapshot.subgenero`
  - `event_snapshot.ciudad`
  - `event_snapshot.recinto_id`
  - `event_snapshot.fecha_evento`
  - `event_snapshot.precio_min`
  - `event_snapshot.precio_max`
  - `event_snapshot.banda_precio`
- completado: incluir `dwell_ms` en `stg_swipes` y `fct_swipes`.
- completado: actualizar tests y descripciones de schema.
