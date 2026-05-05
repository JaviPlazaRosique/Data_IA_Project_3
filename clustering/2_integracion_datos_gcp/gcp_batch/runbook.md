# Runbook del batch semanal de clustering en GCP

## Objetivo

Ejecutar el entrenamiento del clustering como `Cloud Run Job`, leyendo la tabla `dim_user_cluster_features_current` desde BigQuery y dejando listas las tablas que consume la pagina `/recommendations`.

El job cubre de punta a punta la parte de clustering:

1. exporta features elegibles desde BigQuery a CSV temporal;
2. entrena KMeans con `step_4_entrenar_desde_feature_export.py`;
3. carga `user_cluster_assignments`, `cluster_profiles` y `cluster_neighbors` en BigQuery;
4. recalcula `cluster_event_affinity`;
5. recalcula `user_recommendation_candidates`;
6. valida que haya usuarios asignados y recomendaciones generadas.

## Orden recomendado

1. Materializar `dim_user_cluster_features_current` con el job de dbt.
2. Construir y publicar la imagen del job.
3. Desplegar `Cloud Run Job` con una service account dedicada.
4. Probar una ejecucion manual.
5. Programar el job con `Cloud Scheduler` una vez por semana, despues del refresco dbt.

La configuracion Terraform del proyecto lo agenda los lunes a la 01:00 Europe/Madrid, una hora despues del scheduler de dbt de los lunes.

## Buenas practicas incluidas en este scaffold

- `Cloud Run Job` en lugar de servicio HTTP para batch puro.
- variables de entorno explicitas y separadas por responsabilidad.
- service account dedicada.
- logs estructurados en JSON.
- tablas idempotentes con `create or replace table`.
- `model_run_id` por ejecucion para trazabilidad.
- filtros minimos de actividad antes de entrenar.

## Variables principales

- `GCP_PROJECT`: proyecto GCP.
- `BQ_RAW_DATASET`: dataset con `eventos`.
- `BQ_MARTS_DATASET`: dataset de marts donde se escriben outputs y recomendaciones.
- `BQ_FEATURE_DATASET`: dataset donde vive `dim_user_cluster_features_current`.
- `BQ_SOURCE_FEATURE_TABLE`: tabla de features por usuario.
- `MIN_SWIPES_30D` y `MIN_SWIPES_90D`: umbrales minimos para entrar al entrenamiento.
- `MODEL_RUN_ID_PREFIX`: prefijo usado para generar el identificador de ejecucion.
- `LOOKBACK_DAYS`: ventana historica para calcular afinidad cluster-evento.
- `NEIGHBOR_COUNT`: numero de clusters vecinos usados para discovery.
- `MAX_RECOMMENDATIONS_PER_USER`: top-N guardado en `user_recommendation_candidates`.

## Siguientes mejoras opcionales

- versionar metricas y centroides en GCS;
- anadir alertas si el job falla o devuelve 0 usuarios;
- crear un fallback batch de popularidad para usuarios sin cluster o sin candidatos.
