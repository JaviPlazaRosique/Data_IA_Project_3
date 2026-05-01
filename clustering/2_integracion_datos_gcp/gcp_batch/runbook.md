# Runbook del batch de clustering en GCP

## Objetivo

Ejecutar el entrenamiento del clustering como `Cloud Run Job`, leyendo la tabla de features reales desde BigQuery y generando salidas listas para su persistencia posterior.

## Orden recomendado

1. Materializar `dim_user_cluster_features_current` en BigQuery.
2. Construir y publicar la imagen del job.
3. Desplegar `Cloud Run Job` con una service account dedicada.
4. Probar una ejecucion manual.
5. Programar el job con `Cloud Scheduler`.

## Buenas practicas incluidas en este scaffold

- `Cloud Run Job` en lugar de servicio HTTP para batch puro.
- variables de entorno explicitas y separadas por responsabilidad.
- service account dedicada.
- logs estructurados en JSON.
- separacion entre dataset fuente y outputs locales del job.

## Siguientes mejoras recomendadas

- cargar `user_cluster_assignments`, `cluster_profiles` y `cluster_neighbors` de vuelta a BigQuery;
- versionar metricas y centroides en GCS;
- anadir alertas si el job falla o devuelve 0 usuarios;
- mover la lectura desde CSV temporal a persistencia directa en BigQuery para outputs finales.
